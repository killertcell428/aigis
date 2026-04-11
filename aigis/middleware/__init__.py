"""Middleware integrations for aigis.

Each integration requires its own optional dependency:

- FastAPI:    pip install 'aigis[fastapi]'
- LangChain:  pip install 'aigis[langchain]'
- OpenAI:     pip install 'aigis[openai]'
- Anthropic:  pip install 'aigis[anthropic]'
- LangGraph:  pip install 'aigis[langchain]'  (uses langgraph package)

Quick import examples::

    from aigis.middleware.fastapi import AIGuardianMiddleware
    from aigis.middleware.langchain import AIGuardianCallback
    from aigis.middleware.openai_proxy import SecureOpenAI
    from aigis.middleware.anthropic_proxy import SecureAnthropic
    from aigis.middleware.langgraph import GuardNode, GuardianBlockedError
"""
