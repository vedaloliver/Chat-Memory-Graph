from typing import Dict, Optional
from datetime import datetime

from src.app.conversation.models import Conversation, MessageWithTimestamp
from src.app.core.llm_client import ChatMessage


class ConversationStore:
    """
    In-memory conversation store.
    """

    def __init__(self, max_conversations: int = 1000):
        self._conversations: Dict[str, Conversation] = {}
        self.max_conversations = max_conversations

    def create_conversation(self, system_prompt: Optional[str] = None) -> Conversation:
        convo = Conversation()
        if system_prompt:
            convo.add_message(ChatMessage(role="system", content=system_prompt))

        self._conversations[convo.id] = convo
        self._enforce_limit()
        return convo

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        return self._conversations.get(conversation_id)

    def update_conversation(self, conversation: Conversation) -> None:
        self._conversations[conversation.id] = conversation

    def delete_conversation(self, conversation_id: str) -> bool:
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False

    def _enforce_limit(self) -> None:
        if len(self._conversations) > self.max_conversations:
            sorted_items = sorted(
                self._conversations.items(),
                key=lambda item: item[1].updated_at,
            )
            to_remove = len(self._conversations) - self.max_conversations
            for i in range(to_remove):
                del self._conversations[sorted_items[i][0]]
