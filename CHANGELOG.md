# Changelog

## [0.1.2] - 2025-01-17

### Added
- Smart virtual environment detection - automatically finds existing venv, .venv, or other virtual environments
- Support for Poetry projects - detects Poetry configuration and prefers .venv directories
- Saved venv configuration in .claude/venv_info.json for consistent Python executable usage
- Automatic dependency installation for Poetry projects using `poetry install`
- Fallback support for requirements.txt in existing virtual environments
- New venv_utils module for consistent virtual environment handling across all scripts

### Changed
- Installer now uses existing virtual environments instead of always creating new ones
- CLI commands (update, check) now use saved venv information for consistent Python executable
- Enhanced project type detection (Poetry vs standard Python projects)
- Improved virtual environment selection logic (prefers .venv for Poetry projects)

### Fixed
- Fixed issue where installer would create duplicate virtual environments
- Fixed Python executable detection in mixed venv scenarios
- Improved error handling for virtual environment setup

## [0.1.1] - 2025-01-17

### Fixed
- Fixed issue where baseline tests were automatically created for all Python modules during installation
- Improved venv directory filtering in find_modules() to prevent scanning system packages
- Baseline tests are now only created when explicitly requested via 'baseline <module>' command
- Added extra path checks to exclude common virtual environment directories (venv/, .venv/, env/, .env/, site-packages/, lib/, bin/, Scripts/)

### Changed
- Updated update.py to skip automatic baseline test generation during initial installation
- Modified total task count calculation to exclude baseline test creation
- Updated summary message to indicate baseline tests should be created manually

### Added
- Test suite for update.py module to verify venv exclusion works correctly

## [0.1.0] - 2025-01-15

### Initial Release
- Claude Context Box system for managing project context
- Automatic CONTEXT.llm generation and updates
- PROJECT.llm structure mapping
- Integration with Claude AI via CLAUDE.md
- Virtual environment support
- Baseline test generation for safe code modifications