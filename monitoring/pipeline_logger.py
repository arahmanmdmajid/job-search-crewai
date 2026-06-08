# -*- coding: utf-8 -*-
"""
Pipeline Logger
---------------
Captures CrewAI execution events and formats them as clean,
readable markdown for display in the Gradio Pipeline tab.

The core challenge: CrewAI's verbose output uses ANSI terminal color codes
(e.g. [36m, [0m, [1;33m) which look great in a terminal but are
unreadable garbage in a web UI. This module strips all ANSI codes and
rebuilds the log as clean structured markdown.
"""

import io
import re
import sys
from datetime import datetime


# Regex that matches ALL ANSI escape sequences (colors, bold, cursor moves, etc.)
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape codes from a string."""
    return ANSI_ESCAPE.sub('', text)


class PipelineLogger:
    """
    Records all agent events during a crew run and formats them
    for clean display in the Gradio Pipeline tab.
    """

    def __init__(self):
        self.events = []
        self._stdout_buffer = None
        self._old_stdout = None

    def reset(self):
        """Clear logs from the previous run. Called at the start of each search."""
        self.events = []
        self._stdout_buffer = io.StringIO()

    def start_capture(self):
        """Redirect stdout through a Tee so output goes to terminal AND our buffer."""
        self._stdout_buffer = io.StringIO()
        self._old_stdout = sys.stdout
        sys.stdout = _Tee(self._old_stdout, self._stdout_buffer)

    def stop_capture(self):
        """Restore stdout back to normal."""
        if self._old_stdout:
            sys.stdout = self._old_stdout
            self._old_stdout = None

    # ---- CrewAI Callbacks ---- #

    def on_step(self, step_output):
        """Called by CrewAI after every agent thought/action/tool call."""
        self.events.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": "step",
            "content": strip_ansi(str(step_output))[:500],
        })

    def on_task_complete(self, task_output):
        """Called by CrewAI after each of the 4 tasks finishes."""
        self.events.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": "task_complete",
            "content": strip_ansi(str(task_output))[:400],
        })

    # ---- Format for Gradio UI ---- #

    def format_for_display(self) -> str:
        """
        Strips ANSI codes from captured output, then rebuilds it as
        clean structured markdown grouped by agent/task/tool.
        """
        raw = self._stdout_buffer.getvalue() if self._stdout_buffer else ""
        clean = strip_ansi(raw)

        if not clean.strip():
            return "_No pipeline log captured yet. Run a job search first._"

        lines = [l.rstrip() for l in clean.split("\n") if l.strip()]
        sections = []
        current_section = None
        current_lines = []

        def flush():
            if current_section and current_lines:
                sections.append((current_section, list(current_lines)))

        for line in lines:
            # --- Detect section headers based on CrewAI verbose output patterns ---

            if "Crew Execution Started" in line:
                flush(); current_section = "CREW_START"; current_lines = []

            elif "Task Started" in line:
                flush(); current_section = "TASK_START"; current_lines = []

            elif "Task Completed" in line or "Task output:" in line:
                flush(); current_section = "TASK_DONE"; current_lines = []

            elif "Working Agent:" in line or "Agent:" in line and "Action" not in line:
                flush(); current_section = "AGENT"; current_lines = [line]

            elif "Using tool:" in line or "Action:" in line:
                flush(); current_section = "TOOL_CALL"; current_lines = [line]

            elif "Action Input:" in line or "Tool Input:" in line:
                if current_section != "TOOL_CALL":
                    flush(); current_section = "TOOL_CALL"; current_lines = []
                current_lines.append(line)

            elif "Observation:" in line or "Tool Output:" in line:
                flush(); current_section = "TOOL_OUTPUT"; current_lines = []

            elif "Final Answer:" in line or "Final answer:" in line:
                flush(); current_section = "FINAL_ANSWER"; current_lines = [line]

            elif any(k in line for k in ["Error", "ERROR", "FALLBACK", "Retrying", "failed"]):
                flush(); current_section = "ERROR"; current_lines = [line]

            elif "Crew Execution Completed" in line or "Crew execution completed" in line:
                flush(); current_section = "CREW_END"; current_lines = []

            else:
                if current_section:
                    current_lines.append(line)

        flush()

        # --- Render sections as clean markdown ---
        md = ["## Pipeline Execution Log\n", "---\n"]

        for (stype, slines) in sections:
            body = "\n".join(l for l in slines if l.strip())

            if stype == "CREW_START":
                md.append("\n### Crew Started\n")

            elif stype == "TASK_START":
                # Extract task name from the lines
                name_line = next((l for l in slines if "Name:" in l or "Search" in l
                                  or "Research" in l or "Analyse" in l or "Match" in l), "")
                label = name_line.replace("Name:", "").strip()[:120] if name_line else "New Task"
                md.append(f"\n---\n\n#### Task: {label}\n")

            elif stype == "AGENT":
                agent_name = next((l for l in slines if l.strip()), "Agent")
                agent_name = agent_name.replace("Working Agent:", "").strip()
                md.append(f"\n**Agent Running:** `{agent_name}`\n")

            elif stype == "TOOL_CALL":
                tool_line = next((l for l in slines if "Action" in l or "Using tool" in l), "")
                tool_name = tool_line.replace("Action:", "").replace("Using tool:", "").strip()
                input_lines = [l for l in slines if "Input" in l or "Action" not in l]
                input_text = " ".join(input_lines).replace("Action Input:", "").replace("Tool Input:", "").strip()
                md.append(f"\n> **Tool Called:** `{tool_name}`\n")
                if input_text:
                    md.append(f"> **Input:** {input_text[:200]}\n")

            elif stype == "TOOL_OUTPUT":
                output_text = body.replace("Observation:", "").replace("Tool Output:", "").strip()
                if output_text:
                    md.append(f"> **Tool Output:**\n> {output_text[:400]}\n")

            elif stype == "FINAL_ANSWER":
                answer = body.replace("Final Answer:", "").replace("Final answer:", "").strip()
                md.append(f"\n**Task Result (Summary):** {answer[:300]}...\n")

            elif stype == "TASK_DONE":
                md.append("\n**Task completed.**\n")

            elif stype == "ERROR":
                md.append(f"\n> **[FALLBACK/ERROR]** {body}\n")

            elif stype == "CREW_END":
                md.append("\n---\n\n### Crew Finished\n")

        # --- Append task completion events from callbacks ---
        task_events = [e for e in self.events if e["type"] == "task_complete"]
        if task_events:
            md.append("\n---\n\n## Task Completion Timeline\n")
            agent_names = [
                "Job Researcher",
                "Salary Analyst",
                "Job Analyst",
                "Career Advisor",
            ]
            for i, ev in enumerate(task_events):
                agent = agent_names[i] if i < len(agent_names) else f"Agent {i+1}"
                preview = ev["content"][:200].replace("\n", " ").strip()
                md.append(f"- **[{ev['time']}] {agent} finished:** {preview}...\n")

        return "\n".join(md)


class _Tee:
    """
    Writes to two streams simultaneously.
    Stdout goes to BOTH the real terminal (so you see live output)
    AND the buffer (so we can display it in the Gradio UI).
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


# Shared singleton -- used by both crew.py and app.py
pipeline_logger = PipelineLogger()
