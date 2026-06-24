# Test

## Python Environment

Initializing uv:

```bash
uv init
uv venv
uv sync
```

Syncing up project:

```bash
uv sync
```

### Running Application with inputs:

Inline code
```bash
uv run python main.py --code "def add(a, b): return a + b"
```
File (or stdin with -)
```bash
uv run python main.py --file path/to/code.py
```
GitHub PR (public repos only; URL or short form)

```bash
uv run python main.py --pr https://github.com/owner/repo/pull/123

uv run python main.py --pr owner/repo#123
```

Built-in demo (same sample as before)
```bash
uv run python main.py --demo
```

### Designated Outputs 
```bash
uv run python main.py --demo --output "report_pr-#2.md"
```

## Technologies

1. Python 3.12
2. Google ADK
