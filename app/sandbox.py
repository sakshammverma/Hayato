import subprocess
import tempfile
import os
from dataclasses import dataclass

@dataclass
class SandboxResult:
    passed:bool
    flake8_issues:list[str]
    bandit_issues:list[str]
    syntax_valid: bool

def extract_added_lines(patch: str) -> str:
    lines=[]
    for line in patch.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            lines.append(line[1:])
    return "\n".join(lines)

def run_sandbox(patch: str, filename: str) -> SandboxResult: 

    if not filename.endswith(".py"):
        return SandboxResult(
            passed=True,
            flake8_issues=[],
            bandit_issues=[],
            syntax_valid=True
        )
    code= extract_added_lines(patch)

    if not code.strip():
        return SandboxResult(passed=True, flake8_issues=[], bandit_issues=[], syntax_valid=True)

    with tempfile.NamedTemporaryFile(
        suffix=".py", mode="w", delete=False, 
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        # Check 1, syntax valid or no
        syntax = subprocess.run(
            ["python", "-m", "py_compile", tmp_path],
            capture_output=True, text=True
        )
        syntax_valid = syntax.returncode == 0

        # Check 2, flake8
        flake = subprocess.run(
            ["flake8", "--max-line-length=120", tmp_path],
            capture_output=True, text=True
        )
        flake8_issues = [
            line for line in flake.stdout.split("\n") if line.strip()
        ]

        # Check 3, bandit security scan
        bandit = subprocess.run(
            ["bandit", "-q", tmp_path],
            capture_output=True, text=True
        )
        bandit_issues = [
            line for line in bandit.stdout.split("\n") if line.strip()
        ]

        passed = syntax_valid and len(flake8_issues) == 0

        return SandboxResult(
            passed=passed,
            flake8_issues=flake8_issues,
            bandit_issues=bandit_issues,
            syntax_valid=syntax_valid
        )
    finally:
        os.unlink(tmp_path)  