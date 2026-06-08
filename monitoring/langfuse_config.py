# -*- coding: utf-8 -*-
"""
Langfuse Monitoring Configuration
-----------------------------------
Langfuse is an open-source observability platform for LLM applications.
It records every LLM call, tool call, agent step, input, output,
latency, and token usage -- all visible in a web dashboard.

HOW IT WORKS with CrewAI (Langfuse v4):
  Two layers of tracing are set up:

  Layer 1 -- LiteLLM callbacks:
    CrewAI uses LiteLLM for all LLM calls.
    Setting litellm.success_callback = ["langfuse"] tells LiteLLM to
    automatically send every LLM request/response to Langfuse.

  Layer 2 -- @observe decorator:
    We wrap the entire crew run with langfuse's @observe decorator.
    This creates a named parent trace in the Langfuse dashboard so all
    the individual LLM calls are grouped under one logical workflow trace.

WHAT GETS TRACKED:
  - Every LLM call (prompt, response, model, token count, cost)
  - Each agent step and tool call
  - Total workflow duration
  - Errors and failed steps

Dashboard: https://cloud.langfuse.com
"""

import os
from dotenv import load_dotenv

load_dotenv()


def setup_langfuse() -> bool:
    """
    Activates Langfuse tracing via LiteLLM callbacks.
    Must be called BEFORE the crew runs.

    Returns True if monitoring was successfully enabled, False otherwise.
    """
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    host = os.getenv("LANGFUSE_BASE_URL", os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"))

    if not (secret_key and public_key):
        print("[Langfuse] Monitoring DISABLED -- set LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY in .env")
        return False

    # Set LANGFUSE_HOST explicitly -- LiteLLM looks for this name specifically
    os.environ["LANGFUSE_HOST"] = host
    os.environ["LANGFUSE_SECRET_KEY"] = secret_key
    os.environ["LANGFUSE_PUBLIC_KEY"] = public_key

    # Activate LiteLLM -> Langfuse integration
    # This routes every LLM call made inside CrewAI agents to Langfuse
    try:
        import litellm
        if "langfuse" not in litellm.success_callback:
            litellm.success_callback.append("langfuse")
        if "langfuse" not in litellm.failure_callback:
            litellm.failure_callback.append("langfuse")
        print("[Langfuse] Monitoring ENABLED -- LiteLLM callbacks activated")
        print(f"   Dashboard: {host}")
        print("   All LLM calls will be traced automatically.\n")
        return True
    except Exception as e:
        print(f"[Langfuse] WARNING -- Could not activate LiteLLM callbacks: {e}")
        return False


def get_observe_decorator():
    """
    Returns Langfuse's @observe decorator if available.
    Used in crew.py to wrap the entire crew run as a single named trace.

    In Langfuse v4, observe is imported directly from langfuse:
        from langfuse import observe
    """
    try:
        from langfuse import observe
        return observe
    except ImportError:
        # Return a no-op decorator if langfuse is not available
        def noop(name=None):
            def decorator(fn):
                return fn
            return decorator
        return noop


def get_monitoring_status() -> dict:
    """
    Returns the current monitoring configuration as a dict.
    Used by the UI to show whether monitoring is active.
    """
    return {
        "enabled": bool(
            os.getenv("LANGFUSE_SECRET_KEY") and os.getenv("LANGFUSE_PUBLIC_KEY")
        ),
        "host": os.getenv("LANGFUSE_BASE_URL", os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")),
    }
