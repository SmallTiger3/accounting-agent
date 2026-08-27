from typing import Optional
from langchain_core.language_models import BaseChatModel
from ..core.config import settings


def create_llm() -> BaseChatModel:
    """根据配置创建LLM实例"""
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "deepseek":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.LLM_MODEL or "deepseek-chat",
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL or "https://api.deepseek.com",
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=4096,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.LLM_MODEL or "gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=4096,
        )
    elif provider == "mimo":
        # MiMo如果兼容OpenAI格式，可以直接用ChatOpenAI
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.LLM_MODEL or "mimo-chat",
            api_key=settings.MIMO_API_KEY,
            base_url=settings.MIMO_BASE_URL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=4096,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
