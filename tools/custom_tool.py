# -*- coding: utf-8 -*-
"""
custom_tool.py
--------------
This file is the entry point for our custom-built tool: the Resume Matcher.

The Resume Matcher is the tool we built from scratch (not from an existing API
wrapper or library). It takes a candidate's profile and a job description,
then uses GPT-4o-mini to produce a structured match score (0-100) with
strengths, skill gaps, and a hire recommendation.

Why this is a "custom tool":
  - It is NOT a wrapper around a pre-existing API like Tavily or Remotive
  - The scoring logic, prompt engineering, and output format were designed
    specifically for this project
  - It solves a problem (resume-job matching) that no off-the-shelf tool covers

The actual implementation lives in tools/resume_tool.py.
This file re-exports it so the assignment folder structure is satisfied.
"""

from tools.resume_tool import resume_matcher_tool

# Re-export so this file can be imported as the custom tool
__all__ = ["resume_matcher_tool"]
