import os
import asyncio
from dotenv import load_dotenv
from litellm import completion

load_dotenv()

async def review_file(
    pr_title: str,
    pr_description: str,
    repository_name: str,
    file_path: str,
    risk_level: str,
    diff: str   
) -> str:
    if risk_level == "low":
        model = "groq/llama-3.1-8b-instant"
    else:
        model = "groq/llama-3.3-70b-versatile"

    user_prompt = f"""PR Title:
    
{pr_title}

PR Description:
{pr_description}

Repository:
{repository_name}

File:
{file_path}

Risk Level:
{risk_level}

Diff:

{diff}

Review this pull request according to the system instructions.
"""
    system_prompt ='''
You are a Senior Software Engineer, Security Reviewer, and Code Quality Auditor with expertise in:

* Secure software development
* Backend and frontend engineering
* Performance optimization
* Software architecture
* Production reliability

Your job is to review pull request changes and identify:

* Security vulnerabilities
* Logic errors and bugs
* Performance issues
* Reliability concerns
* Scalability risks
* Maintainability problems
* Missing validation or error handling
* Test coverage gaps

Focus only on issues that matter in production.

Ignore:

* Whitespace changes
* Comment formatting
* Personal style preferences
* Naming suggestions unless they reduce readability or introduce bugs

Reference exact line numbers whenever possible.

Structure your response EXACTLY like this:

## Summary

One-line assessment of the PR.

## Issues Found

For each issue:

### Issue N

* Severity: Critical | High | Medium | Low
* Line: <line number>
* Category: Security | Bug | Performance | Reliability | Maintainability | Testing
* Problem: <what is wrong>
* Impact: <why it matters>
* Fix: <recommended change>

## Positives

* List good engineering practices found in the PR.

## Verdict

APPROVE | REQUEST CHANGES | NEEDS DISCUSSION

Only report issues with reasonable confidence.
Do not speculate about code that is not present in the diff.
'''
     
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt}
    ]
    response = await asyncio.to_thread(completion, model=model, messages=messages)
    return response.choices[0].message.content  # type: ignore