# -*- coding: utf-8 -*-
"""
Gradio Web Interface
--------------------
Three tabs:
  Tab 1 - Job Search     : user inputs + final report output
  Tab 2 - Pipeline Log   : live log of every agent step, tool call, task completion
  Tab 3 - About          : architecture explanation for the assignment
"""

import gradio as gr
from crew import run_job_search_crew
from monitoring.langfuse_config import get_monitoring_status
from monitoring.pipeline_logger import pipeline_logger


# ------------------------------------------------------------------ #
# Run function -- wired to the Search button
# ------------------------------------------------------------------ #
def run_search(job_title, location, candidate_profile, job_description):
    """
    Runs the 4-agent crew and yields updates to BOTH outputs:
      - output_result : the final career report
      - output_log    : the pipeline execution log (shown in Tab 2)
    """

    # --- Input validation (fallback before crew even starts) ---
    if not job_title.strip():
        yield "Please enter a job title.", "No run started."
        return

    if not candidate_profile.strip() or len(candidate_profile.strip()) < 30:
        yield (
            "Please enter a more detailed skills/experience profile (at least a few sentences).",
            "No run started."
        )
        return

    user_inputs = {
        "job_title":          job_title.strip(),
        "location":           location.strip() or "Remote",
        "candidate_profile":  candidate_profile.strip(),
        "job_description":    job_description.strip() or "Not provided",
    }

    # --- Stage 1: Show "running" status while crew works ---
    yield (
        "**Running... this takes 1-2 minutes.**\n\n"
        "The 4 agents are working in sequence:\n\n"
        "1. Job Researcher    -- searching for live listings...\n"
        "2. Salary Analyst    -- researching compensation data...\n"
        "3. Job Analyst       -- summarizing the job description...\n"
        "4. Career Advisor    -- scoring your profile fit...\n\n"
        "_Switch to the **Pipeline Log** tab to watch the agents work in real time "
        "after the run completes._",
        "Pipeline log will appear here once the run finishes..."
    )

    # --- Stage 2: Run the crew ---
    result = run_job_search_crew(user_inputs)

    # --- Stage 3: Yield the final report + the captured pipeline log ---
    final_report = (
        "## Your Personalised Job Search Report\n\n"
        + result
        + "\n\n---\n*Check the **Pipeline Log** tab to see how the agents produced this report.*"
    )

    pipeline_log = pipeline_logger.format_for_display()

    yield final_report, pipeline_log


def clear_all():
    return "", "Remote", "", "", \
           "*Results will appear here after you run the search.*", \
           "*Pipeline log will appear here after a run.*"


# ------------------------------------------------------------------ #
# Build the UI
# ------------------------------------------------------------------ #
def build_ui():

    monitoring = get_monitoring_status()
    mon_status = (
        "Monitoring: ON -- traces sent to Langfuse"
        if monitoring["enabled"]
        else "Monitoring: OFF -- add Langfuse keys to .env"
    )

    with gr.Blocks(title="Job Search CrewAI") as demo:

        # ---- Header ----
        gr.Markdown(
            "# Job Search CrewAI Assistant\n"
            "### Multi-agent AI system: finds jobs, researches salaries, scores your fit\n"
            "*CrewAI + GPT-4o-mini + Tavily + Remotive + Langfuse*"
        )
        gr.Markdown(f"`{mon_status}`")

        # ============================================================
        # TAB 1 -- Job Search
        # ============================================================
        with gr.Tab("Job Search"):

            gr.Markdown(
                "Fill in your details and click **Run Job Search**. "
                "Four specialist AI agents will collaborate to produce your report. "
                "Switch to **Pipeline Log** after the run to see each agent's work."
            )

            with gr.Row():
                job_title = gr.Textbox(
                    label="Job Title (required)",
                    placeholder="e.g. Data Scientist, Backend Developer, Product Manager",
                    value="Data Scientist",
                    scale=2,
                )
                location = gr.Textbox(
                    label="Location / Work Type",
                    placeholder="e.g. Malaysia, Remote, Singapore",
                    value="Remote",
                    scale=1,
                )

            candidate_profile = gr.Textbox(
                label="Your Skills & Experience (required)",
                placeholder=(
                    "Describe your background, skills, experience, and education.\n\n"
                    "Example: 3 years Python, pandas, scikit-learn. BSc Computer Science. "
                    "Built customer churn model. Familiar with SQL and Tableau."
                ),
                lines=5,
            )

            job_description = gr.Textbox(
                label="Job Description to Analyse (optional -- paste a specific posting)",
                placeholder=(
                    "Paste a job posting here. The Job Analyst will summarize it "
                    "and the Career Advisor will score your fit against it.\n\n"
                    "Leave empty to let agents work from search results only."
                ),
                lines=7,
            )

            with gr.Row():
                run_btn  = gr.Button("Run Job Search", variant="primary",   size="lg")
                clear_btn = gr.Button("Clear",          variant="secondary", size="lg")

            output_result = gr.Markdown(
                value="*Results will appear here after you run the search.*"
            )

        # ============================================================
        # TAB 2 -- Pipeline Log  (KEY TAB for assignment demonstration)
        # ============================================================
        with gr.Tab("Pipeline Log"):

            gr.Markdown(
                "## How the Agents Collaborate\n\n"
                "This tab shows the **internal working** of the multi-agent system. "
                "Run a job search in Tab 1, then come back here to see:\n\n"
                "- Which agent ran at each step\n"
                "- Which tools were called and with what input\n"
                "- What each tool returned\n"
                "- How tasks were completed and passed to the next agent\n"
                "- Any errors or fallback events\n\n"
                "---"
            )

            # Static workflow diagram
            gr.Markdown(
                "### Workflow Diagram\n\n"
                "```\n"
                "User Input (job title, location, profile, job description)\n"
                "     |\n"
                "     v\n"
                "+-----------------------------+\n"
                "| TASK 1: Job Researcher      |  Tool: Tavily Search API\n"
                "| Find live job listings      |  --> Returns: 3-5 job postings\n"
                "+-----------------------------+\n"
                "     |\n"
                "     v\n"
                "+-----------------------------+\n"
                "| TASK 2: Salary Analyst      |  Tool: Remotive API\n"
                "| Research compensation data  |  --> Returns: salary ranges\n"
                "+-----------------------------+\n"
                "     |\n"
                "     v\n"
                "+-----------------------------+\n"
                "| TASK 3: Job Analyst         |  Tool: GPT Summarizer (custom)\n"
                "| Summarize job description   |  --> Returns: structured summary\n"
                "+-----------------------------+\n"
                "     |\n"
                "     v  (receives outputs from Tasks 1, 2, 3 as context)\n"
                "+-----------------------------+\n"
                "| TASK 4: Career Advisor      |  Tool: Resume Matcher (custom)\n"
                "| Score fit + final report    |  --> Returns: score, gaps, next steps\n"
                "+-----------------------------+\n"
                "     |\n"
                "     v\n"
                "Final Report shown in Tab 1 + saved to outputs/\n"
                "```\n\n"
                "---\n\n"
                "### Last Run -- Live Agent Log\n"
                "_Run a search in Tab 1 to populate this log._"
            )

            output_log = gr.Markdown(
                value="*Pipeline log will appear here after a run.*"
            )

            if monitoring["enabled"]:
                gr.Markdown(
                    f"\n**Langfuse Dashboard:** [{monitoring['host']}]({monitoring['host']})\n\n"
                    "Full traces (LLM calls, token counts, latency) are also "
                    "recorded there automatically."
                )

        # ============================================================
        # TAB 3 -- About / Architecture
        # ============================================================
        with gr.Tab("About This Project"):
            gr.Markdown(
                "## About This Application\n\n"
                "A **CrewAI multi-agent job search assistant** extended from the original "
                "[job-search-assistant](https://github.com/arahmanmdmajid/job-search-assistant) "
                "(built with LangGraph).\n\n"
                "---\n\n"
                "## Core Requirements Covered\n\n"
                "| Requirement | Implementation |\n"
                "|---|---|\n"
                "| 3+ CrewAI agents | 4 agents: Researcher, Salary Analyst, Job Analyst, Career Advisor |\n"
                "| 3+ tasks | 4 tasks with sequential process and context passing |\n"
                "| 3+ tools | Tavily search, Remotive salary, GPT summarizer, Resume Matcher |\n"
                "| 1 custom tool | Resume Matcher -- scores candidate fit 0-100 |\n"
                "| Fallback logic | Per-tool try/except + crew-level retry with friendly errors |\n"
                "| Langfuse monitoring | LiteLLM callbacks + @observe trace wrapping |\n"
                "| MCP awareness | Documented in README -- tools described as future MCP servers |\n\n"
                "---\n\n"
                "## Agents & Tools\n\n"
                "| Agent | Tool | Purpose |\n"
                "|---|---|---|\n"
                "| Job Market Researcher | Tavily Search API | Find live job listings |\n"
                "| Salary Analyst | Remotive API | Research compensation benchmarks |\n"
                "| Job Description Analyst | GPT-4o-mini Summarizer | Structure job postings |\n"
                "| Career Advisor | Resume Matcher (custom) | Score candidate-job fit 0-100 |\n\n"
                "---\n\n"
                "## Fallback Handling\n\n"
                "**Tool level** -- every tool catches:\n"
                "- Timeout errors\n"
                "- Connection errors\n"
                "- Invalid API keys (HTTP 401/403)\n"
                "- Empty or too-short inputs\n\n"
                "**Crew level** (`fallback/fallback_handler.py`):\n"
                "- Retries the full crew run up to 2 times\n"
                "- Waits between retries (handles rate limits)\n"
                "- Returns a structured, friendly error message if all retries fail\n\n"
                "---\n\n"
                "## MCP Awareness\n\n"
                "Tools that could become MCP servers:\n"
                "- **Tavily job search** -- standardised search endpoint for any agent\n"
                "- **Remotive salary tool** -- shared salary data source across projects\n"
                "- **Resume Matcher** -- reusable career-fit scoring microservice\n\n"
                "Benefits: tools discoverable at runtime, no duplicated wrappers, "
                "agents from any framework can call them.\n\n"
                "---\n\n"
                "*Built with: CrewAI, OpenAI GPT-4o-mini, Tavily, Remotive, Langfuse, Gradio*"
            )

        # ---- Wire button to BOTH outputs ----
        run_btn.click(
            fn=run_search,
            inputs=[job_title, location, candidate_profile, job_description],
            outputs=[output_result, output_log],
        )

        clear_btn.click(
            fn=clear_all,
            outputs=[
                job_title, location, candidate_profile, job_description,
                output_result, output_log,
            ],
        )

    return demo


# ------------------------------------------------------------------ #
# Entry point
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(),
    )
