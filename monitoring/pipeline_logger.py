# -*- coding: utf-8 -*-
"""
Pipeline Logger
---------------
This module captures every step of the CrewAI workflow and formats it
as readable log messages for display in the Gradio UI.

WHY THIS MATTERS for the assignment:
  The pipeline log is what "shows" the examiner that:
    - Multiple agents are collaborating (each agent appears in the log)
    - Tools are being used (tool calls are recorded)
    - Fallback logic is working (errors and retries are logged)
    - The workflow is sequential and structured (tasks appear in order)

HOW IT WORKS:
  CrewAI Crew accepts two optional callbacks:
    - step_callback: fires after every agent action (thinking, tool call, response)
    - task_callback: fires after every task completes

  We pass our logger's methods as these callbacks, so every internal event
  gets recorded. We also capture stdout so the raw verbose output is saved.

  The formatted log is then shown in the Gradio "Pipeline" tab.
"""

import io
import sys
from datetime import datetime


class PipelineLogger:
    """
    Records all agent events during a crew run and formats them
    for display in the UI.
    """

    def __init__(self):
        self.events = []           # structured event records
        self._stdout_buffer = None # captures raw verbose output
        self._old_stdout = None

    def reset(self):
        """Clear logs from previous run. Called at the start of each new search."""
        self.events = []
        self._stdout_buffer = io.StringIO()

    def start_capture(self):
        """Redirect stdout so CrewAI's verbose print statements are captured."""
        self._stdout_buffer = io.StringIO()
        self._old_stdout = sys.stdout
        # We use a Tee so output goes to BOTH the buffer AND the real terminal
        sys.stdout = _Tee(self._old_stdout, self._stdout_buffer)

    def stop_capture(self):
        """Restore stdout back to normal."""
        if self._old_stdout:
            sys.stdout = self._old_stdout
            self._old_stdout = None

    # ---- CrewAI Callbacks ---- #

    def on_step(self, step_output):
        """
        Called by CrewAI after every agent action.
        An 'action' could be: thinking, calling a tool, or producing a response.
        """
        self.events.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": "step",
            "content": str(step_output)[:500],  # cap length
        })

    def on_task_complete(self, task_output):
        """
        Called by CrewAI after each task finishes.
        This tells us an agent has finished its assigned work.
        """
        self.events.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": "task_complete",
            "content": str(task_output)[:300],
        })

    # ---- Formatting for UI ---- #

    def format_for_display(self) -> str:
        """
        Formats the captured stdout into a clean, readable markdown log.
        Highlights agent names, tool calls, and errors with labels.
        """
        raw = self._stdout_buffer.getvalue() if self._stdout_buffer else ""

        if not raw.strip():
            return "_No pipeline log captured. Make sure verbose=True in crew.py_"

        lines = raw.split("\n")
        formatted = []
        formatted.append("## Pipeline Execution Log\n")
        formatted.append("---\n")

        for line in lines:
            line = line.rstrip()
            if not line:
                continue

            # Tag lines based on content for visual structure
            if any(k in line for k in ["Working Agent:", "Agent:", ">> Agent"]):
                formatted.append(f"\n### {line}")

            elif any(k in line for k in ["Task:", "## Task", "Task output:"]):
                formatted.append(f"\n**{line}**")

            elif any(k in line for k in ["Using tool:", "Action:", "Action Input:", "Tool Input:"]):
                formatted.append(f"\n> **TOOL CALL:** `{line}`")

            elif any(k in line for k in ["Observation:", "Tool Output:", "Result:"]):
                formatted.append(f"> **TOOL OUTPUT:** {line}")

            elif any(k in line for k in ["Final Answer:", "Final answer:"]):
                formatted.append(f"\n**FINAL ANSWER:** {line}")

            elif any(k in line for k in ["ERROR", "Error", "FALLBACK", "failed", "Failed"]):
                formatted.append(f"\n> **[ERROR/FALLBACK]** {line}")

            elif any(k in line for k in ["Retrying", "retry", "attempt"]):
                formatted.append(f"> **[RETRY]** {line}")

            elif line.startswith("=") or line.startswith("-"):
                formatted.append(f"\n{line}")

            else:
                formatted.append(line)

        # Append structured callback events
        if self.events:
            formatted.append("\n\n---\n## Task Completion Summary\n")
            for ev in self.events:
                if ev["type"] == "task_complete":
                    formatted.append(
                        f"- **[{ev['time']}] Task completed:** "
                        f"{ev['content'][:150]}..."
                    )

        return "\n".join(formatted)

    def get_summary(self) -> str:
        """
        Returns a short summary of what ran -- shown at the top of the pipeline tab.
        """
        task_count = sum(1 for e in self.events if e["type"] == "task_complete")
        step_count = sum(1 for e in self.events if e["type"] == "step")
        return (
            f"**Run completed:** {task_count} tasks finished, "
            f"{step_count} agent steps recorded."
        )


class _Tee:
    """
    A helper that writes to TWO streams at once.
    Used so stdout goes to BOTH the terminal (so you see it live)
    AND the buffer (so we can display it in the UI).
    """
    def __init__(self, stream1, stream2):
        self.stream1 = stream1
        self.stream2 = stream2

    def write(self, data):
        self.stream1.write(data)
        self.stream2.write(data)

    def flush(self):
        self.stream1.flush()
        self.stream2.flush()

    def fileno(self):
        return self.stream1.fileno()


# Shared singleton -- the same logger instance is used by crew.py and app.py
pipeline_logger = PipelineLogger()
