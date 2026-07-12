# TopTrackTracker

## Commands
- Test: `pytest`
- Lint: `ruff check . && ruff format .`

## Conventions
- Type hints on all public functions
- Prefer pathlib over os.path
- Tests live in tests/, mirroring the module layout

## Before finishing any task
Run the linter and the test suite. Do not open a PR with failing tests.