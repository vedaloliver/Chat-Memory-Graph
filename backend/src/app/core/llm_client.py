from typing import Sequence, Dict, Any
from pydantic import BaseModel

import openai
from openai import AsyncOpenAI

from src.app.core.config import get_settings


class AppError(Exception):
    """Base application error class for clean error handling."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ChatMessage(BaseModel):
    """Model representing a chat message."""
    role: str  # "user", "assistant", "system"
    content: str


class LlmClient:
    """Client for communicating with OpenAI's LLM API (standard or Azure)."""
    
    def __init__(self, api_key: str, model: str, use_azure: bool = False, azure_endpoint: str = "", azure_api_version: str = "") -> None:
        """
        Initialize the LLM client with API key and model.
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model name to use
            use_azure: Whether to use Azure OpenAI
            azure_endpoint: Azure OpenAI endpoint URL
            azure_api_version: Azure OpenAI API version
        """
        if use_azure and azure_endpoint:
            # For Azure OpenAI, we need to construct the URL with the API version included
            deployment_url = f"{azure_endpoint}/openai/deployments/{model}/chat/completions"
            if azure_api_version:
                deployment_url += f"?api-version={azure_api_version}"
                
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=azure_endpoint,  # Just the base endpoint
            )
            # For Azure, we don't include the model in the request but store the full path
            self.model = ""
            self.azure_deployment = model
            self.deployment_url = deployment_url
        else:
            self.client = AsyncOpenAI(api_key=api_key)
            self.model = model
            self.azure_deployment = None
    
    async def chat(self, messages: Sequence[ChatMessage]) -> str:
        """
        Sends the full chat history to the LLM and returns the assistant reply text.
        
        Args:
            messages: Sequence of chat messages
            
        Returns:
            Assistant's reply as a string
            
        Raises:
            AppError: On API error or unexpected response format
        """
        try:
            # Convert messages to the format expected by the OpenAI API
            openai_messages = [
                {"role": msg.role, "content": msg.content} 
                for msg in messages
            ]
            
            # Make the API call - different approach for Azure vs standard OpenAI
            if self.azure_deployment:
                # For Azure OpenAI, we need to make a direct API call
                import httpx
                
                headers = {
                    "Content-Type": "application/json",
                    "api-key": self.client.api_key,
                }
                
                payload = {"messages": openai_messages}
                
                async with httpx.AsyncClient() as http_client:
                    api_response = await http_client.post(
                        self.deployment_url,
                        headers=headers,
                        json=payload,
                        timeout=30.0
                    )
                    
                    if api_response.status_code != 200:
                        error_message = f"Azure OpenAI API error: {api_response.text}"
                        raise AppError(error_message, api_response.status_code)
                    
                    response_data = api_response.json()
                    
                    # Create a compatible response object structure
                    class Choice:
                        def __init__(self, message_content):
                            self.message = type('Message', (), {'content': message_content})()
                    
                    class Response:
                        def __init__(self, choices):
                            self.choices = choices
                    
                    response = Response([Choice(response_data['choices'][0]['message']['content'])])
            else:
                # Standard OpenAI call
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=openai_messages
                )
            
            # Extract and return the assistant's reply
            if not response.choices or len(response.choices) == 0:
                raise AppError("LLM returned empty response", 502)
            
            return response.choices[0].message.content
        
        except openai.APIError as e:
            raise AppError(f"OpenAI API error: {str(e)}", 502)
        except openai.APIConnectionError as e:
            raise AppError(f"Failed to connect to OpenAI API: {str(e)}", 503)
        except openai.RateLimitError as e:
            raise AppError(f"OpenAI rate limit exceeded: {str(e)}", 429)
        except openai.AuthenticationError as e:
            raise AppError(f"OpenAI authentication error: {str(e)}", 401)
        except httpx.ConnectError as e:
            # More detailed connection error information
            import socket
            msg = f"Connection error: {str(e)}"
            if isinstance(e.__cause__, socket.gaierror):
                msg += " - DNS resolution failed for the host. Check your AZURE_OPENAI_ENDPOINT setting."
            raise AppError(msg, 503)
        except Exception as e:
            raise AppError(f"Unexpected error during LLM request: {str(e)}")


def get_llm_client() -> LlmClient:
    """
    Create and return an LLM client using application settings.
    For use with FastAPI dependency injection.
    """
    settings = get_settings()
    return LlmClient(
        api_key=settings.openai_api_key, 
        model=settings.openai_model,
        use_azure=settings.use_azure,
        azure_endpoint=settings.azure_endpoint,
        azure_api_version=settings.azure_api_version
    )
