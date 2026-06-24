from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SourceType = Literal["string", "file", "github_pr"]

_GITHUB_PR_URL_RE = re.compile(
    r"^https?://(?:www\.)?github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)/?$"
)
_GITHUB_PR_SHORT_RE = re.compile(
    r"^(?P<owner>[^/]+)/(?P<repo>[^/]+)#(?P<number>\d+)$"
)

class InputError(ValueError):
    """Raised when user input cannot be resolved."""

@dataclass(frozen=True)
class ResolvedCodeInput:
    code: str
    source_type: SourceType
    source_label: str

def parse_github_pr_ref(pr_ref: str) -> tuple[str, str, int]:
    ref = pr_ref.strip()
    match = _GITHUB_PR_URL_RE.match(ref) or _GITHUB_PR_SHORT_RE.match(ref)
    if not match:
        raise InputError(
            "Invalid GitHub PR reference. Use a URL like "
            "https://github.com/owner/repo/pull/123 or owner/repo#123."
        )
    return match.group("owner"), match.group("repo"), int(match.group("number"))


def load_code_from_file(path: str | Path) -> str:
    file_path = Path(path)
    if str(path) == "-":
        import sys

        code = sys.stdin.read()
        if not code.strip():
            raise InputError("No code received from stdin.")
        return code

    if not file_path.is_file():
        raise InputError(f"File not found: {file_path}")

    try:
        code = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise InputError(f"File is not valid UTF-8 text: {file_path}") from exc

    if not code.strip():
        raise InputError(f"File is empty: {file_path}")

    return code


def fetch_github_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch a PR diff from the public GitHub API (no auth required)."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github.diff",
            "User-Agent": "code-review-agent",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            diff = response.read().decode("utf-8")
    except HTTPError as exc:
        if exc.code == 404:
            raise InputError(
                f"GitHub PR not found: {owner}/{repo}#{pr_number}"
            ) from exc
        if exc.code == 403:
            raise InputError(
                "GitHub API rate limit reached. Try again later or use --file/--code instead."
            ) from exc
        raise InputError(f"GitHub API error ({exc.code}): {exc.reason}") from exc
    except URLError as exc:
        raise InputError(f"Could not reach GitHub API: {exc.reason}") from exc

    if not diff.strip():
        raise InputError(f"GitHub PR has no diff: {owner}/{repo}#{pr_number}")

    return diff

# String Input
def resolve_string_input(code: str) -> ResolvedCodeInput:
    if not code.strip():
        raise InputError("Code string is empty.")
    return ResolvedCodeInput(
        code=code,
        source_type="string",
        source_label="inline code",
    )


# File Input
def resolve_file_input(path: str) -> ResolvedCodeInput:
    code = load_code_from_file(path)
    label = "stdin" if path == "-" else str(Path(path))
    return ResolvedCodeInput(
        code=code,
        source_type="file",
        source_label=label,
    )

# Github Input
def resolve_github_pr_input(pr_ref: str) -> ResolvedCodeInput:
    owner, repo, pr_number = parse_github_pr_ref(pr_ref)
    code = fetch_github_pr_diff(owner, repo, pr_number)
    return ResolvedCodeInput(
        code=code,
        source_type="github_pr",
        source_label=f"{owner}/{repo}#{pr_number}",
    )

# Main function to resolve the code input
def resolve_code_input(
    *,
    code: str | None = None,
    file: str | None = None,
    pr: str | None = None,
) -> ResolvedCodeInput:
    sources = [value for value in (code, file, pr) if value is not None]
    if len(sources) != 1:
        raise InputError("Provide only one of the following: string, file path, or GitHub PR.")

    if code is not None:
        return resolve_string_input(code)
    if file is not None:
        return resolve_file_input(file)
    return resolve_github_pr_input(pr)
