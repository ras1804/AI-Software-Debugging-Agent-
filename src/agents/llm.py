from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.config.settings import get_settings


class LLMClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.enabled = bool(settings.openai_api_key)
        self.llm = ChatOpenAI(model=settings.openai_model, temperature=settings.llm_temperature, api_key=settings.openai_api_key) if self.enabled else None

    def invoke(self, system: str, user: str) -> str:
        if not self.llm:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        response = self.llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return str(response.content)

    def with_tools(self, tools: list[Any]):
        if not self.llm:
            return None
        return self.llm.bind_tools(tools)
