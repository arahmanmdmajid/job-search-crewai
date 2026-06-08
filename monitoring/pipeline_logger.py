# -*- coding: utf-8 -*-
"""
Pipeline Logger
---------------
Captures CrewAI execution events, strips ANSI terminal codes, and
formats everything as clean readable markdown for the Gradio Pipeline tab.

Produces:
  1. Run Summary table  -- total time, agents completed, tool calls, errors
  2. Agent Timing Bars  -- ASCII bar chart showing relative agent durations
  3. Execution Log      -- cleaned, structured step-by-step agent activity
  4. Task Timeline      -- completion timestamps from CrewAI callbacks
"""

import io
import re
import sys
from datetime import datetime


# Matches ALL ANSI escape sequences (colors, bold, cursor, box-drawing wrappers)
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

AGENT_NAMES = [
    "Job Researcher",
    "Salary Analyst",
    "Job Analyst",
    "Career Advisor",
]


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape codes from a string."""
    return ANSI_ESCAPE.sub('', text)


def _ascii_bar(value: float, max_value: float, width: int = 20) -> str:
    """Build a filled ASCII progress bar. e.g. ████████░░░░░░░░░░░░"""
    if max_value == 0:
        return "░" * width
    filled = round((value / max_value) * width)
    return "█" * filled + "░" * (width - filled)


class PipelineLogger:

    def __init__(self):
        self.events = []
        self.run_start: datetime = None
        self.run_end:   datetime = None
        self._stdout_buffer = None
        self._old_stdout = None

    def reset(self):
        """Clear all state from the previous run."""
        self.events = []
        self.run_start = datetime.now()
        self.run_end = None
        self._stdout_buffer = io.StringIO()

    def start_capture(self):
        """Tee stdout so output goes to terminal AND our buffer."""
        self._stdout_buffer = io.StringIO()
        self._old_stdout = sys.stdout
        sys.stdout = _Tee(self._old_stdout, self._stdout_buffer)

    def stop_capture(self):
        """Restore normal stdout and record run end time."""
        if self._old_stdout:
            sys.stdout = self._old_stdout
            self._old_stdout = None
        self.run_end = datetime.now()

    # ---- CrewAI Callbacks ---- #

    def on_step(self, step_output):
        """Fires after every agent thought/action/tool call."""
        content = strip_ansi(str(step_output))
        self.events.append({
            "dt":      datetime.now(),
            "type":    "step",
            "content": content[:500],
            "is_tool": any(k in content.lower() for k in
                           ["action:", "using tool", "tool input"]),
            "is_error": any(k in content.lower() for k in
                            ["error", "fallback", "failed", "exception"]),
        })

    def on_task_complete(self, task_output):
        """Fires after each of the 4 tasks finishes."""
        self.events.append({
            "dt":      datetime.now(),
            "type":    "task_complete",
            "content": strip_ansi(str(task_output))[:400],
        })

    # ---- Formatting ---- #

    def format_for_display(self) -> str:
        """
        Returns the full pipeline log as clean markdown with:
          - Run summary stats table
          - ASCII timing bars per agent
          - Structured execution log (ANSI-stripped)
          - Task completion timeline
        """
        parts = []
        parts.append(self._build_summary_section())
        parts.append(self._build_timing_section())
        parts.append(self._build_execution_log())
        parts.append(self._build_task_timeline())
        return "\n\n".join(p for p in parts if p.strip())

    # ------------------------------------------------------------------ #
    # Section 1: Run Summary
    # ------------------------------------------------------------------ #
    def _build_summary_section(self) -> str:
        if not self.run_start:
            return "_No run data yet. Run a job search first._"

        end = self.run_end or datetime.now()
        total_secs = (end - self.run_start).total_seconds()

        task_done  = sum(1 for e in self.events if e["type"] == "task_complete")
        tool_calls = sum(1 for e in self.events if e.get("is_tool"))
        errors     = sum(1 for e in self.events if e.get("is_error"))
        steps      = sum(1 for e in self.events if e["type"] == "step")

        mins = int(total_secs // 60)
        secs = total_secs % 60
        time_str = f"{mins}m {secs:.1f}s" if mins > 0 else f"{secs:.1f}s"

        return (
            "## Run Summary\n\n"
            "| Metric | Value |\n"
            "|---|---|\n"
            f"| Total run time | **{time_str}** |\n"
            f"| Agents completed | **{task_done} / 4** |\n"
            f"| Agent steps recorded | **{steps}** |\n"
            f"| Tool calls made | **{tool_calls}** |\n"
            f"| Errors / Fallbacks | **{errors}** |"
        )

    # ------------------------------------------------------------------ #
    # Section 2: ASCII Timing Bars
    # ------------------------------------------------------------------ #
    def _build_timing_section(self) -> str:
        task_events = [e for e in self.events if e["type"] == "task_complete"]

        if not task_events or not self.run_start:
            return ""

        # Calculate each agent's duration
        # Task 1 starts at run_start; each subsequent task starts when the previous ended
        durations = []
        prev_dt = self.run_start
        for ev in task_events:
            dur = (ev["dt"] - prev_dt).total_seconds()
            durations.append(max(dur, 0.1))   # floor at 0.1s to avoid zero bars
            prev_dt = ev["dt"]

        total    = sum(durations)
        max_dur  = max(durations)
        BAR_W    = 20

        lines = ["## Agent Timing Breakdown\n"]
        lines.append("```")
        lines.append(f"{'Agent':<22} {'Bar':<22} {'Time':>6}  {'Share':>6}")
        lines.append("-" * 60)

        for i, dur in enumerate(durations):
            name  = AGENT_NAMES[i] if i < len(AGENT_NAMES) else f"Agent {i+1}"
            bar   = _ascii_bar(dur, max_dur, BAR_W)
            pct   = (dur / total * 100) if total > 0 else 0
            lines.append(f"{name:<22} {bar}  {dur:>5.1f}s  {pct:>5.1f}%")

        lines.append("-" * 60)
        lines.append(f"{'Total':<22} {'':22}  {total:>5.1f}s  100.0%")
        lines.append("```")

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Section 3: Execution Log (ANSI-stripped + structured)
    # ------------------------------------------------------------------ #
    def _build_execution_log(self) -> str:
        raw = self._stdout_buffer.getvalue() if self._stdout_buffer else ""
        clean = strip_ansi(raw)

        if not clean.strip():
            return ""

        lines = [l.rstrip() for l in clean.split("\n") if l.strip()]
        sections = []
        current_type  = None
        current_lines = []

        def flush():
            if current_type and current_lines:
                sections.append((current_type, list(current_lines)))

        for line in lines:
            if "Crew Execution Started" in line:
                flush(); current_type = "CREW_START"; current_lines = []

            elif "Task Started" in line:
                flush(); current_type = "TASK_START"; current_lines = []

            elif "Task Completed" in line or "Task output:" in line:
                flush(); current_type = "TASK_DONE"; current_lines = []

            elif "Working Agent:" in line or ("Agent:" in line and "Action" not in line):
                flush(); current_type = "AGENT"; current_lines = [line]

            elif "Using tool:" in line or "Action:" in line:
                flush(); current_type = "TOOL_CALL"; current_lines = [line]

            elif "Action Input:" in line or "Tool Input:" in line:
                if current_type != "TOOL_CALL":
                    flush(); current_type = "TOOL_CALL"; current_lines = []
                current_lines.append(line)

            elif "Observation:" in line or "Tool Output:" in line:
                flush(); current_type = "TOOL_OUTPUT"; current_lines = []

            elif "Final Answer:" in line or "Final answer:" in line:
                flush(); current_type = "FINAL_ANSWER"; current_lines = [line]

            elif any(k in line for k in ["ERROR", "Error", "FALLBACK", "Retrying", "failed"]):
                flush(); current_type = "ERROR"; current_lines = [line]

            elif "Crew Execution Completed" in line:
                flush(); current_type = "CREW_END"; current_lines = []

            else:
                if current_type:
                    current_lines.append(line)

        flush()

        md = ["## Execution Log\n", "---"]

        for (stype, slines) in sections:
            body = "\n".join(l for l in slines if l.strip())

            if stype == "CREW_START":
                md.append("\n**Crew started.**")

            elif stype == "TASK_START":
                label = next(
                    (l.replace("Name:", "").strip()[:100]
                     for l in slines if "Name:" in l or any(
                         k in l for k in ["Search","Research","Analyse","Match","Summar"])),
                    "New Task"
                )
                md.append(f"\n---\n\n#### Task: {label}")

            elif stype == "AGENT":
                name = slines[0].replace("Working Agent:", "").replace("Agent:", "").strip()
                md.append(f"\n**Agent:** `{name}`")

            elif stype == "TOOL_CALL":
                tool = next(
                    (l.replace("Action:", "").replace("Using tool:", "").strip()
                     for l in slines if "Action" in l or "Using tool" in l),
                    "Unknown tool"
                )
                inp = " ".join(
                    l.replace("Action Input:", "").replace("Tool Input:", "").strip()
                    for l in slines if "Input" in l
                )
                md.append(f"\n> **Tool Called:** `{tool}`")
                if inp:
                    md.append(f"> **Input:** {inp[:200]}")

            elif stype == "TOOL_OUTPUT":
                out = body.replace("Observation:", "").replace("Tool Output:", "").strip()
                if out:
                    md.append(f"> **Tool Output:** {out[:350]}")

            elif stype == "FINAL_ANSWER":
                ans = body.replace("Final Answer:", "").replace("Final answer:", "").strip()
                md.append(f"\n**Task Result:** {ans[:250]}...")

            elif stype == "TASK_DONE":
                md.append("\n**Task completed.**")

            elif stype == "ERROR":
                md.append(f"\n> **[FALLBACK / ERROR]** {body}")

            elif stype == "CREW_END":
                md.append("\n---\n\n**Crew finished.**")

        return "\n".join(md)

    # ------------------------------------------------------------------ #
    # Section 4: Task Timeline
    # ------------------------------------------------------------------ #
    def _build_task_timeline(self) -> str:
        task_events = [e for e in self.events if e["type"] == "task_complete"]
        if not task_events:
            return ""

        lines = ["## Task Completion Timeline\n"]
        for i, ev in enumerate(task_events):
            agent = AGENT_NAMES[i] if i < len(AGENT_NAMES) else f"Agent {i+1}"
            preview = ev["content"][:180].replace("\n", " ").strip()
            lines.append(f"- **[{ev['dt'].strftime('%H:%M:%S')}] {agent}:** {preview}...")

        return "\n".join(lines)


class _Tee:
    """Writes to two streams simultaneously (terminal + buffer)."""
    def __init__(self, s1, s2):
        self.s1, self.s2 = s1, s2

    def write(self, data):
        self.s1.write(data)
        self.s2.write(data)

    def flush(self):
        self.s1.flush()
        self.s2.flush()

    def fileno(self):
        return self.s1.fileno()


# Shared singleton used by crew.py and app.py
pipeline_logger = PipelineLogger()
