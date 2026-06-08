"""
Crew Assembly
-------------
This file is the HEART of the application.
It brings together agents + tasks and kicks off the workflow.

Think of it as the "project manager" that:
  1. Hires the agents (imports from agents.py)
  2. Assigns the work (imports from tasks.py)
  3. Decides the process (sequential vs hierarchical)
  4. Starts the crew and returns the final result

PROCESS TYPES in CrewAI:
  - Process.sequential  → Tasks run ONE AFTER ANOTHER (like an assembly line)
  - Process.hierarchical → A manager agent decides who does what (more complex)

We use SEQUENTIAL here because our workflow has a clear order:
  Research → [Salary + Summarize in parallel] → Match & Advise
"""

from crewai import Crew, Process
from agents import create_agents
from tasks import create_tasks
from monitoring.langfuse_config import setup_langfuse
from fallback.fallback_handler import safe_crew_run


def run_job_search_crew(user_inputs: dict) -> str:
    """
    Main entry point. Builds and runs the crew.

    Args:
        user_inputs: dict with:
            - job_title (str)
            - location (str)
            - candidate_profile (str)
            - job_description (str)

    Returns:
        Final report as a string.
    """

    # Step 1: Set up Langfuse monitoring (tracks everything that happens)
    setup_langfuse()

    # Step 2: Create all agents
    agents = create_agents()

    # Step 3: Create all tasks, injecting the user's inputs
    tasks = create_tasks(agents, user_inputs)

    # Step 4: Assemble the Crew
    crew = Crew(
        agents=list(agents),
        tasks=tasks,
        process=Process.sequential,
        # sequential means:
        #   Task 1 runs → Task 2 runs → Task 3 runs → Task 4 runs
        #   Each task can see previous tasks' outputs via context=[...]
        verbose=True,
        # verbose=True prints a live log of what each agent is thinking
        # and doing — great for learning and debugging!
    )

    # Step 5: Run the crew with fallback protection
    # (if something crashes, fallback_handler catches it gracefully)
    result = safe_crew_run(crew, user_inputs)

    return result
