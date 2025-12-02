# src/app/core/llm/memory_client.py

from typing import Any, Dict, Optional
import json

from .base_client import BaseOpenAIClient
from .errors import AppError


class MemoryLlmClient:
    """
    LiCo-style memory extraction client.

    Uses a dedicated prompt + JSON response_format to extract:
      - session_summary
      - entities
      - triples
    from a dialogue chunk.
    """

    def __init__(self, base_client: BaseOpenAIClient) -> None:
        self._base = base_client

    @classmethod
    def from_base(cls, base_client: BaseOpenAIClient) -> "MemoryLlmClient":
        return cls(base_client)

    async def extract_memory(
        self,
        chunk_text: str,
        existing_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Use the LLM to extract LiCo-style memory structures from a dialogue chunk.

        Returns a dict with the shape:

        {
          "session_summary": {
            "summary_text": str,
            "keywords": [str, ...],
            "themes": [str, ...]
          },
          "entities": [
            {
              "canonical_name": str,
              "entity_type": str | null,
              "aliases": [str, ...]
            },
            ...
          ],
          "triples": [
            {
              "subject": str,
              "subject_type": str | null,
              "object": str | null,
              "object_type": str | null,
              "relation_type": str,
              "relation_text": str | null,
              "importance": float | null,
              "is_state": bool | null,
              "confidence": float | null
            },
            ...
          ]
        }
        """
        if self._base.azure_deployment:
            # Keep Azure path simple for now; you can implement this later if you want.
            raise AppError(
                "Memory extraction is not yet implemented for Azure OpenAI deployments."
            )

        system_prompt = (
            "You are a memory extraction module for a long-term conversational agent.\n"
            "Given a short dialogue chunk, you must extract:\n"
            "  - A concise session summary update\n"
            "  - A small set of important entities\n"
            "  - A small set of salient entity–relation triples\n\n"
            "Return ONLY a JSON object with this exact structure:\n"
            "{\n"
            '  \"session_summary\": {\n'
            '    \"summary_text\": string,        // brief overall summary for the session so far\n'
            '    \"keywords\": string[],          // key nouns / concepts\n'
            '    \"themes\": string[]             // coarse themes like \"work\", \"relationship\", etc.\n'
            "  },\n"
            '  \"entities\": [\n'
            "    {\n"
            '      \"canonical_name\": string,    // short name, e.g. \"Oliver\", \"Hazal\", \"PVM project\"\n'
            '      \"entity_type\": string|null,  // e.g. \"person\", \"project\", \"emotion\", \"place\"\n'
            '      \"aliases\": string[]          // other surface forms, can be empty\n'
            "    }, ...\n"
            "  ],\n"
            '  \"triples\": [\n'
            "    {\n"
            '      \"subject\": string,           // SHOULD match one of entities.canonical_name when possible\n'
            '      \"subject_type\": string|null,\n'
            '      \"object\": string|null,       // another entity name or short phrase\n'
            '      \"object_type\": string|null,\n'
            '      \"relation_type\": string,     // short verb-like label, e.g. \"feels\", \"works_on\"\n'
            '      \"relation_text\": string|null,// natural language paraphrase of the relation\n'
            '      \"importance\": number|null,   // 0.0–1.0, higher = more important\n'
            '      \"is_state\": boolean|null,    // true if it is an ongoing state, false if event-like\n'
            '      \"confidence\": number|null    // 0.0–1.0, how confident you are\n'
            "    }, ...\n"
            "  ]\n"
            "}\n\n"
            "Rules:\n"
            "- Focus on psychologically and semantically important facts (preferences, relationships, goals, "
            "strong emotions, longer-term projects). Ignore trivial chit-chat.\n"
            "- Prefer a handful of high-quality entities and triples over many low-quality ones.\n"
            "- If something is unknown, use null instead of inventing.\n"
            "- Do NOT include any extra keys outside this schema.\n"
        )

        payload = {
            "chunk": chunk_text,
            "existing_session_summary": existing_summary or "",
        }

        try:
            response = await self._base.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": (
                            "Here is the latest dialogue chunk and the previous session summary "
                            "(if any). Respond with a single JSON object only.\n\n"
                            f"{json.dumps(payload, ensure_ascii=False)}"
                        ),
                    },
                ],
                response_format={"type": "json_object"},
            )

            if not getattr(response, "choices", None) or len(response.choices) == 0:
                raise AppError("Memory extraction LLM returned empty response", 502)

            raw = response.choices[0].message.content
            data = json.loads(raw)

            if not isinstance(data, dict):
                raise AppError(
                    "Memory extraction response was not a JSON object", 502
                )

            # Normalise keys so the rest of the code can rely on them existing
            data.setdefault("session_summary", {})
            data.setdefault("entities", [])
            data.setdefault("triples", [])

            if not isinstance(data["entities"], list):
                data["entities"] = []
            if not isinstance(data["triples"], list):
                data["triples"] = []
            if not isinstance(data["session_summary"], dict):
                data["session_summary"] = {}

            return data

        except json.JSONDecodeError as e:
            raise AppError(f"Failed to parse memory extraction JSON: {str(e)}")
        except AppError:
            # Just bubble up AppError from base client unchanged
            raise
        except Exception as e:
            raise AppError(f"Unexpected error during memory extraction: {str(e)}")
