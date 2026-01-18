Tasks:
1) Create pyproject.toml using uv (uv init) for Python 3.12.
2) Add dependencies and dev dependencies.
3) Create package skeleton files:
   - src/stencilify/__init__.py
   - src/stencilify/cli.py
   - src/stencilify/logging.py
   - src/stencilify/constants.py
4) Implement a stub CLI: `stencilify --help` and `stencilify generate --help` work.
5) Configure ruff (format + lint) and mypy (basic strictness but practical).
6) Add pytest config and one trivial test that imports the CLI module.

Deliverables:
- All files committed in working tree (no need to actually git commit, just create files).
- Show the exact uv commands you ran and confirm `uv run stencilify --help` works.

Keep code typed (type hints), and prefer dataclasses or pydantic models for configs.
