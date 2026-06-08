---
title: Job Search CrewAI Assistant
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: "4.44.1"
app_file: app.py
pinned: false
python_version: "3.11"
short_description: Multi-agent job search assistant built with CrewAI
---

# Job Search CrewAI Assistant

An AI-powered job search assistant built with **CrewAI**, featuring a multi-agent workflow that finds jobs, researches salaries, summarizes job descriptions, and scores candidate fit -- all with observability via Langfuse.

This project is an extension of the original [job-search-assistant](https://github.com/arahmanmdmajid/job-search-assistant) (built with LangGraph), rebuilt using CrewAI's multi-agent framework.

---

## Use Case

Job seekers often spend hours searching for listings, researching salaries, reading lengthy job descriptions, and trying to evaluate if they are a good fit. This assistant automates that entire process through four specialist AI agents working in sequence.

**Why an agentic workflow instead of a single prompt?**
A single LLM call cannot search the web, query salary APIs, and reason about a candidate profile all at once. By splitting responsibilities across agents, each one can focus, use the right tool, and pass structured output to the next -- producing a much more reliable and detailed result.

---

## Project Structure

```
job-search-crewai/
|
+-- app.py                   <- Gradio web interface
+-- crew.py                  <- Assembles and runs the crew
+-- agents.py                <- Defines all 4 agents
+-- tasks.py                 <- Defines all 4 tasks
|
+-- tools/
|   +-- custom_tool.py       <- Entry point for the custom Resume Matcher tool
|   +-- resume_tool.py       <- Custom Resume Matcher implementation
|   +-- search_tool.py       <- Tavily job search tool
|   +-- salary_tool.py       <- Remotive salary research tool
|   +-- summarizer_tool.py   <- GPT-4o-mini job description summarizer
|
+-- fallback/
|   +-- fallback_handler.py  <- Retry logic and graceful error handling
|
+-- monitoring/
|   +-- langfuse_config.py   <- Langfuse observability setup
|   +-- pipeline_logger.py   <- Live pipeline log with timing bars
|
+-- data/
|   +-- sample_input.txt     <- Sample inputs for testing
|
+-- outputs/
|   +-- sample_result.md     <- Example of a generated report
|
+-- test_setup.py            <- Verifies API keys and package installation
+-- requirements.txt
+-- .env.example
+-- README.md
```

---

## Agents

| Agent | Role | Tool | Responsibility |
|---|---|---|---|
| Job Market Researcher | Searches for live job listings | Tavily Search API | Finds 3-5 relevant job postings |
| Salary Analyst | Researches compensation data | Remotive API | Reports salary ranges and benchmarks |
| Job Description Analyst | Summarizes job postings | GPT-4o-mini summarizer | Breaks job descriptions into structured sections |
| Career Advisor | Evaluates candidate fit | Resume Matcher (custom) | Scores fit 0-100, identifies gaps, gives next steps |

---

## Tools

### 1. Job Search Tool (`tools/search_tool.py`)
- **What it does:** Queries the Tavily API for live job listings
- **Used by:** Job Market Researcher agent
- **Input:** Search query string (e.g. "Data Scientist remote jobs")
- **Output:** Formatted list of job titles, companies, URLs, and descriptions

### 2. Salary Research Tool (`tools/salary_tool.py`)
- **What it does:** Queries the Remotive API for salary data in remote job postings
- **Used by:** Salary Analyst agent
- **Input:** Job title string (e.g. "Data Scientist")
- **Output:** Salary ranges found in listings, with notes if data is unavailable

### 3. Job Description Summarizer (`tools/summarizer_tool.py`)
- **What it does:** Uses GPT-4o-mini to structure a raw job posting into sections
- **Used by:** Job Description Analyst agent
- **Input:** Raw job description text
- **Output:** Role Overview, Responsibilities, Required Skills, Nice-to-Haves, Red Flags

### 4. Resume Matcher -- Custom Tool (`tools/custom_tool.py`, `tools/resume_tool.py`)
- **What it does:** Scores how well a candidate matches a job (0-100)
- **Used by:** Career Advisor agent
- **Input:** Candidate profile + job description (separated by `---`)
- **Output:** Match score, strengths, skill gaps, and hire recommendation
- **Why custom:** No off-the-shelf API provides resume-to-job fit scoring with this level of structured output. The prompt and scoring logic were designed specifically for this project.

---

## Workflow

The crew runs as a **sequential process**:

```
User inputs (job title, location, candidate profile, job description)
     |
     v
Task 1: Job Researcher searches for listings      [job_search_tool]
     |
     v
Task 2: Salary Analyst researches pay             [salary_tool]
     |
     v
Task 3: Job Analyst summarizes job description    [summarizer_tool]
     |
     v (receives outputs from Tasks 1, 2, and 3 as context)
Task 4: Career Advisor scores fit + final report  [resume_matcher_tool]
```

---

## Fallback Handling

Fallbacks are implemented at two levels:

**Tool level** (in each tool file):
- Every tool wraps API calls in try/except blocks
- Specific errors are caught: Timeout, ConnectionError, HTTPError
- Each returns a user-readable FALLBACK message instead of crashing

**Crew level** (`fallback/fallback_handler.py`):
- The crew is retried up to 2 times on failure
- Retries include a wait period (5s, then 10s) to handle rate limits
- After all retries fail, a structured fallback message is returned

---

## Monitoring and Observability (Langfuse)

This project uses [Langfuse](https://cloud.langfuse.com) for full observability.

**What is tracked:**
- Every agent execution (who ran, when, how long)
- Every LLM call (prompt, response, token count)
- Every tool call (tool name, input, output)
- Errors and failed steps
- Total latency and cost estimation

---

## MCP (Model Context Protocol) Awareness

**Tools that could become MCP servers:**
- **Job Search Tool:** Exposed as an MCP server so any agent can call it without reimplementing the API client
- **Salary Research Tool:** A standardised MCP data source shareable across career-related projects
- **Resume Matcher:** Deployed as an MCP server, reusable by any agent in any framework

**Benefits of MCP here:**
- Tool definitions standardised -- no duplicating `@tool` wrappers
- New agents can dynamically discover and call tools at runtime
- Resume Matcher becomes a reusable microservice for any career app

---

## Setup (Local)

```bash
git clone https://github.com/arahmanmdmajid/job-search-crewai.git
cd job-search-crewai
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # fill in your API keys
python test_setup.py         # verify everything works
python app.py                # open http://localhost:7860
```

## Setup (HuggingFace Spaces)

Add these as **Secrets** in your Space settings:

| Secret | Where to get it |
|---|---|
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) |
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) |
| `LANGFUSE_SECRET_KEY` | [cloud.langfuse.com](https://cloud.langfuse.com) |
| `LANGFUSE_PUBLIC_KEY` | [cloud.langfuse.com](https://cloud.langfuse.com) |
| `LANGFUSE_BASE_URL` | `https://cloud.langfuse.com` |

---

## Technologies Used

| Technology | Purpose |
|---|---|
| [CrewAI](https://crewai.com) | Multi-agent orchestration framework |
| [OpenAI GPT-4o-mini](https://platform.openai.com) | LLM powering all agents |
| [Tavily](https://tavily.com) | Real-time web search API |
| [Remotive](https://remotive.com/api) | Remote job and salary data API |
| [Langfuse](https://langfuse.com) | LLM observability and tracing |
| [Gradio](https://gradio.app) | Web UI framework |

---

## Original Project

This extends the original job-search-assistant built with LangGraph:
https://github.com/arahmanmdmajid/job-search-assistant

| Feature | Original (LangGraph) | This Project (CrewAI) |
|---|---|---|
| Architecture | Single agent with tool loop | 4 specialist agents |
| Workflow | Agent decides tool use | Structured sequential tasks |
| Observability | None | Langfuse full tracing + Pipeline tab |
| Fallback | Basic try/except | Retry logic + friendly messages |
| Output | Chat response | Structured career report |
