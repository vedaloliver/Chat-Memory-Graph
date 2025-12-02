# src/app/core/llm/base_client.py

from typing import Any, Dict, List, Optional

import httpx
import openai
from openai import AsyncOpenAI
import socket

from .errors import AppError


class BaseOpenAIClient:
    """
    Low-level OpenAI/Azure client.

    - Handles AsyncOpenAI construction
    - Handles Azure vs standard OpenAI routing
    - Normalises errors into AppError
    - Exposes a single awaitable: create_chat_completion()
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        use_azure: bool = False,
        azure_endpoint: str = "",
        azure_api_version: str = "",
    ) -> None:
        self.model = model
        self.azure_deployment: Optional[str] = None
        self.deployment_url: Optional[str] = None

        if use_azure and azure_endpoint:
            # Azure OpenAI: explicit deployment URL (chat/completions)
            deployment_url = f"{azure_endpoint}/openai/deployments/{model}/chat/completions"
            if azure_api_version:
                deployment_url += f"?api-version={azure_api_version}"

            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=azure_endpoint,
            )
            self.azure_deployment = model
            self.deployment_url = deployment_url
        else:
            # Standard OpenAI
            self.client = AsyncOpenAI(api_key=api_key)
            self.azure_deployment = None
            self.deployment_url = None

    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> Any:
        """
        Create a chat completion using either Azure or standard OpenAI.

        Returns:
            A response object with a `.choices` list where each choice has
            `.message.content`, matching the OpenAI Python client shape.

        Raises:
            AppError on any API / network issue.
        """
        try:
            if self.azure_deployment:
                # Azure OpenAI: direct HTTP call via httpx
                if not self.deployment_url:
                    raise AppError("Azure deployment URL is not configured", 500)

                headers = {
                    "Content-Type": "application/json",
                    "api-key": self.client.api_key,  # type: ignore[attr-defined]
                }

                payload: Dict[str, Any] = {"messages": messages}
                payload.update(kwargs)

                async with httpx.AsyncClient() as http_client:
                    api_response = await http_client.post(
                        self.deployment_url,
                        headers=headers,
                        json=payload,
                        timeout=30.0,
                    )

                if api_response.status_code != 200:
                    error_message = f"Azure OpenAI API error: {api_response.text}"
                    raise AppError(error_message, api_response.status_code)

                response_data = api_response.json()
                choices = response_data.get("choices") or []
                if not choices:
                    raise AppError("Azure OpenAI API returned empty choices", 502)

                content = (
                    choices[0]
                    .get("message", {})
                    .get("content", "")
                )

                # Build a minimal OpenAI-like response object
                class _Message:
                    def __init__(self, content: str) -> None:
                        self.content = content

                class _Choice:
                    def __init__(self, message: _Message) -> None:
                        self.message = message

                class _Response:
                    def __init__(self, choices: List[_Choice]) -> None:
                        self.choices = choices

                return _Response([_Choice(_Message(content))])

            # Standard OpenAI: use official client
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs,
            )
            return response

        except openai.APIError as e:
            raise AppError(f"OpenAI API error: {str(e)}", 502)
        except openai.APIConnectionError as e:
            raise AppError(f"Failed to connect to OpenAI API: {str(e)}", 503)
        except openai.RateLimitError as e:
            raise AppError(f"OpenAI rate limit exceeded: {str(e)}", 429)
        except openai.AuthenticationError as e:
            raise AppError(f"OpenAI authentication error: {str(e)}", 401)
        except httpx.ConnectError as e:
            msg = f"Connection error: {str(e)}"
            if isinstance(e.__cause__, socket.gaierror):
                msg += (
                    " - DNS resolution failed for the host. "
                    "Check your AZURE_OPENAI_ENDPOINT setting."
                )
            raise AppError(msg, 503)
        except Exception as e:
            raise AppError(f"Unexpected error during LLM request: {str(e)}")
