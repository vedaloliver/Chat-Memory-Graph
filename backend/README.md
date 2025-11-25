# LLM Service

A simple, clean Python service that exposes an HTTP API endpoint to interact with language models like OpenAI's GPT.

## Features

- Stateless API for LLM interactions
- Clean, layered architecture with FastAPI
- Simple chat endpoint that forwards messages to LLM
- Type hinted with Pydantic models
- Dependency injection patterns

## Project Structure

```
.
├─ pyproject.toml       # Dependency management with Poetry
├─ README.md           # This file
├─ .env                # Environment variables (not committed)
├─ src/
│  └─ app/
│     ├─ main.py       # FastAPI app entrypoint
│     ├─ api/
│     │  └─ routes_chat.py   # API routes
│     ├─ core/
│     │  ├─ config.py        # Settings / env handling
│     │  └─ llm_client.py    # LLM client abstraction
│     └─ models/
│        └─ chat.py          # Pydantic models
└─ tests/
   └─ test_chat_api.py       # API tests
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   poetry install
   ```
   
3. Copy `.env.example` to `.env` and set your OpenAI API key:
   ```
   cp .env.example .env
   ```

4. Run the service:
   ```
   uvicorn src.app.main:app --reload
   ```

5. API is available at http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Chat endpoint: POST http://localhost:8000/api/chat

## Environment Variables

- `OPENAI_API_KEY`: Required for LLM API access
- `OPENAI_MODEL`: Optional, defaults to "gpt-4.1-mini"
- `DEBUG`: Optional, set to "true" to enable debug mode

## Testing

Run tests with:

```
pytest
```
