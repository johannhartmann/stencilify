# Architecture Decisions and Tradeoffs

This is an append-only log of key decisions, conflicts resolved, and tradeoffs made during development.

---

## 2026-01-18: Project Initialization

**Decision**: Created tracking framework before Step 1 implementation
**Rationale**: Ensures all subsequent steps are auditable and reproducible
**Tradeoff**: None; this is scaffolding only

---

## 2026-01-18: Step 1 - CLI Framework Choice

**Decision**: Initially chose Click for CLI implementation
**Rationale**: More widely used and stable than alternatives
**Tradeoff**: None at the time

---

## 2026-01-18: Step 2 - Switch to Typer

**Decision**: Replaced Click with Typer for CLI implementation
**Rationale**: Step 2 prompt explicitly requested Typer for CLI parsing
**Change**: Step 1 used Click, Step 2 requirement superseded this choice
**Impact**:
  - Required rewrite of cli.py
  - Typer provides better type hints integration
  - Dependency change: removed click, added typer
  - Entry point changed from cli:main to cli:cli_main
**Tradeoff**: Minor rewrite effort, but better alignment with prompt requirements

---

## 2026-01-18: Step 2 - Pydantic Model Structure

**Decision**: Use separate Color class instead of Pydantic model
**Rationale**:
  - Needed luminance calculation for automatic palette sorting
  - Store colors as strings in config for simplicity
  - Parse to Color objects only when needed
**Tradeoff**: Slight duplication of validation logic, but cleaner separation

---

## 2026-01-18: Step 2 - List Defaults in CLI

**Decision**: Use `None` instead of `[]` for list parameter defaults
**Rationale**: Avoids B006 linting error (mutable default arguments)
**Implementation**: Handle with `palette or []` and `lock or []` in function body
**Tradeoff**: Extra null check, but follows Python best practices

---
