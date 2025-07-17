# Changelog

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