# Contributing to pendle-py

Thanks for your interest in improving `pendle-py`! This guide covers the local
setup and the quality bar every change must meet.

## Development setup

The project targets **Python 3.9+** and is developed against a real 3.9
interpreter to catch version-specific issues early.

```bash
git clone https://github.com/robertruben98/pendle-py
cd pendle-py
uv venv --python 3.9 && source .venv/bin/activate
uv pip install -e ".[dev]"
```

(If you don't use `uv`, a plain `python -m venv .venv && pip install -e ".[dev]"`
works too.)

## Workflow

1. Branch off `main` (e.g. `feat/...`, `fix/...`, `docs/...`).
2. **Write tests first.** This project follows test-driven development: add a
   failing test, then the minimal code to pass it. Unit tests must not hit the
   network — mock HTTP with `respx`. Live calls go in tests marked
   `@pytest.mark.integration`, which are deselected by default.
3. Keep changes focused and small. Commit messages use the `feat:` / `fix:` /
   `chore:` / `docs:` style; do not add AI co-author trailers.
4. Open a pull request against `main`. CI (lint + the 3.9–3.13 test matrix) must
   be green before review.

## Quality gates

All of these must pass locally before you push:

```bash
ruff check .            # lint
ruff format --check .   # formatting
mypy                    # strict type checking
pytest                  # unit tests (respx-mocked)
pytest -m integration   # live API tests (optional; hits the real network)
```

## Compatibility notes

- `requires-python` is `>=3.9`, and CI tests on a real 3.9 interpreter. Avoid
  PEP 604 `X | None` in runtime-evaluated annotations (pydantic models, function
  signatures); use `typing.Optional` / `Union` / `List` / `Dict`. The relevant
  `ruff` `UP` rules are disabled to enforce this.
- Models use `extra="allow"` so new API fields don't break parsing — prefer
  adding typed fields over relying on this.
