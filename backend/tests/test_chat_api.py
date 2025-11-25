import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.app.main import app
from src.app.core.llm_client import LlmClient


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_llm_client():
    """
    Fixture that mocks the LLM client to avoid making real API calls during tests.
    """
    with patch('src.app.api.routes_chat.get_llm_client') as mock_get_client:
        # Create a mock LLM client
        mock_client = AsyncMock(spec=LlmClient)
        # Set up the chat method to return a test response
        mock_client.chat.return_value = "This is a mocked LLM response."
        # Configure the get_llm_client function to return our mock
        mock_get_client.return_value = mock_client
        yield mock_client


def test_chat_endpoint_success(client, mock_llm_client):
    """Test successful chat request and response."""
    # Test request data
    test_request = {
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ]
    }
    
    # Make request to the chat endpoint
    response = client.post("/api/chat", json=test_request)
    
    # Verify response
    assert response.status_code == 200
    assert response.json() == {"reply": "This is a mocked LLM response."}
    
    # Verify the mock was called correctly
    mock_llm_client.chat.assert_called_once()


def test_chat_endpoint_empty_messages(client):
    """Test chat request with empty messages list."""
    test_request = {"messages": []}
    
    response = client.post("/api/chat", json=test_request)
    
    # Should succeed as we're not validating message content yet
    assert response.status_code == 200


def test_chat_endpoint_invalid_request(client):
    """Test chat request with invalid format."""
    # Missing required 'messages' field
    test_request = {"wrong_field": "value"}
    
    response = client.post("/api/chat", json=test_request)
    
    # Should fail validation
    assert response.status_code == 422  # Unprocessable Entity
