# -*- coding: utf-8 -*-
"""
Crew Assembly
-------------
This file is the HEART of the application.
It brings together agents + tasks and kicks off the workflow.

Think of it as the "project manager" that:
  1. Activates Langfuse monitoring
  2. Hires the agents (imports from agents.py)
  3. Assigns the work (imports from tasks.py)
  4. Decides the process (sequential vs hierarchical)
  5. Starts the crew and returns the final result

PROCESS TYPES in CrewAI:
  - Process.sequential  -> Tasks run ONE AFTER ANOTHER (like an assembly line)
  - Process.hierarchical -> A manager agent decides who does what (more complex)

We use SEQUENTIAL because our workflow has a clear order:
  Research -> [Salary + Summarize] -> Match & Advise
"""

import os
from datetime import datetime
from crewai import Crew, Process
from agents import create_agents
from tasks import create_tasks
from monitoring.langfuse_config import setup_langfuse, get_observe_decorator
from fallback.fallback_handler import safe_crew_run


def run_job_search_crew(user_inputs: dict) -> str:
    """
    Main entry point. Builds and runs the crew.

    The @observe decorator (from Langfuse) wraps this entire function
    so the whole run appears as ONE trace in the Langfuse dashboard,
    with each LLM call and tool call nested inside it.

    Args:
        user_inputs: dict with:
            - job_title (str)
            - location (str)
            - candidate_profile (str)
            - job_description (str)

    Returns:
        Final report as a string.
    """

    # Step 1: Activate Langfuse monitoring
    # This enables LiteLLM -> Langfuse callbacks so every LLM call is traced
    monitoring_active = setup_langfuse()

    # Step 2: Wrap with Langfuse @observe if monitoring is active
    # The observe decorator creates a parent trace in Langfuse that all
    # nested LLM calls and tool calls appear under
    if monitoring_active:
        result = _run_crew_observed(user_inputs)
    else:
        result = _run_crew(user_inputs)

    # Step 3: Auto-save the result to the outputs/ folder
    _save_result(result, user_inputs)

    return result


def _run_crew_observed(user_inputs: dict) -> str:
    """
    Runs the crew with Langfuse @observe tracing active.
    This creates a named parent trace in Langfuse so you can find it easily.

    In Langfuse v4, @observe is imported directly from langfuse (not langfuse.decorators).
    get_observe_decorator() handles the correct import path.
    """
    observe = get_observe_decorator()

    @observe(name="job-search-crew-run")
    def _inner(inputs):
        return _run_crew(inputs)

    return _inner(user_inputs)


def _run_crew(user_inputs: dict) -> str:
    """
    Core crew execution -- builds agents, tasks, and runs the workflow.
    """
    # Create all agents
    agents = create_agents()

    # Create all tasks, injecting the user's inputs
    tasks = create_tasks(agents, user_inputs)

    # Assemble the Crew
    crew = Crew(
        agents=list(agents),
        tasks=tasks,
        process=Process.sequential,
        # sequential means:
        #   Task 1 runs -> Task 2 runs -> Task 3 runs -> Task 4 runs
        #   Each task can see previous tasks' outputs via context=[...]
        verbose=True,
        # verbose=True prints a live log of what each agent is thinking
        # and doing -- great for learning and debugging!
    )

    # Run the crew with fallback protection
    # (if something crashes, fallback_handler catches it gracefully)
    return safe_crew_run(crew, user_inputs)


def _save_result(result: str, user_inputs: dict):
    """
    Saves the crew's output to the outputs/ folder as a markdown file.
    Filename includes the job title and a timestamp so results don't overwrite each other.
    """
    try:
        os.makedirs("outputs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_title_slug = user_inputs.get("job_title", "result").replace(" ", "_").lower()
        filename = f"outputs/{job_title_slug}_{timestamp}.md"

        header = (
            f"# Job Search Report\n\n"
            f"- **Job Title:** {user_inputs.get('job_title')}\n"
            f"- **Location:** {user_inputs.get('location')}\n"
            f"- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"---\n\n"
        )

        with open(filename, "w", encoding="utf-8") as f:
            f.write(header + result)

        print(f"\nResult saved to: {filename}")

    except Exception as e:
        # Non-critical -- don't crash the app if saving fails
        print(f"[WARN] Could not save result to file: {e}")
