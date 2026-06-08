# -*- coding: utf-8 -*-
"""
Crew Assembly
-------------
This file brings together agents + tasks and kicks off the workflow.

Think of it as the "project manager" that:
  1. Activates Langfuse monitoring
  2. Starts the pipeline logger (captures every agent step for the UI)
  3. Hires the agents (from agents.py)
  4. Assigns the work (from tasks.py)
  5. Runs the crew and returns the final result
"""

import os
from datetime import datetime
from crewai import Crew, Process
from agents import create_agents
from tasks import create_tasks
from monitoring.langfuse_config import setup_langfuse, get_observe_decorator
from monitoring.pipeline_logger import pipeline_logger
from fallback.fallback_handler import safe_crew_run


def run_job_search_crew(user_inputs: dict) -> str:
    """
    Main entry point. Builds and runs the crew.

    Args:
        user_inputs: dict with job_title, location, candidate_profile, job_description

    Returns:
        Final report as a string.
    """
    # Step 1: Activate Langfuse monitoring (traces all LLM calls)
    monitoring_active = setup_langfuse()

    # Step 2: Reset the pipeline logger for this fresh run
    pipeline_logger.reset()

    # Step 3: Run with Langfuse @observe wrapper if monitoring is active
    if monitoring_active:
        result = _run_crew_observed(user_inputs)
    else:
        result = _run_crew(user_inputs)

    # Step 4: Auto-save the result to outputs/
    _save_result(result, user_inputs)

    return result


def _run_crew_observed(user_inputs: dict) -> str:
    """Runs crew wrapped in a Langfuse @observe trace."""
    observe = get_observe_decorator()

    @observe(name="job-search-crew-run")
    def _inner(inputs):
        return _run_crew(inputs)

    return _inner(user_inputs)


def _run_crew(user_inputs: dict) -> str:
    """
    Core crew execution.

    KEY POINT for assignment:
      We pass step_callback and task_callback to the Crew.
      These fire on every agent action and task completion, feeding
      real-time events into the PipelineLogger for display in the UI.
    """
    agents = create_agents()
    tasks = create_tasks(agents, user_inputs)

    crew = Crew(
        agents=list(agents),
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
        # --- Pipeline logging callbacks ---
        # step_callback: fires after every agent thought/action/tool call
        step_callback=pipeline_logger.on_step,
        # task_callback: fires after each of the 4 tasks finishes
        task_callback=pipeline_logger.on_task_complete,
    )

    # Start capturing stdout so verbose agent output appears in the UI log
    pipeline_logger.start_capture()
    try:
        result = safe_crew_run(crew, user_inputs)
    finally:
        # Always restore stdout -- even if the crew crashes
        pipeline_logger.stop_capture()

    return result


def _save_result(result: str, user_inputs: dict):
    """Saves the crew output to outputs/ with a timestamped filename."""
    try:
        os.makedirs("outputs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = user_inputs.get("job_title", "result").replace(" ", "_").lower()
        filename = f"outputs/{slug}_{timestamp}.md"

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
        print(f"[WARN] Could not save result: {e}")
