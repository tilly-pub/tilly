# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build, Test and Lint Commands
- Build package: `./build.sh`
- Run all tests: `./test.sh`
- Run single test: `python -m unittest discover -v -s ./test -p test_cli.py -k test_git_and_til_script`
- Lint code: `ruff check .`
- Publish package: `./publish.sh`

## Code Style Guidelines
- **Indentation**: 4 spaces
- **Line length**: 140 characters (defined in pyproject.toml)
- **Linter**: Ruff (configuration in pyproject.toml)
- **Imports**: Standard library first, then third-party packages
- **Types**: Dynamic typing (no type hints)
- **Naming**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `SCREAMING_SNAKE_CASE`
- **Error handling**: Mix of assertions and try/except blocks
- **Documentation**: Use docstrings with function description when adding new functions
- **Commands**: Defined using Click library with command groups and options