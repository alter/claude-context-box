#!/usr/bin/env python3
"""
Setup script for Claude Context Box
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ""

# Read version
version = "0.1.0"
init_path = Path(__file__).parent / "claude_context" / "__init__.py"
if init_path.exists():
    for line in init_path.read_text().splitlines():
        if line.startswith("__version__"):
            version = line.split('"')[1]
            break

setup(
    name="claude-context-box",
    version=version,
    author="Claude Context Box Contributors",
    description="A context management system for Claude AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alter/claude-context-box",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'claude_context': [
            'templates/*.md',
            'templates/*.llm',
            'scripts/*.py',
            'scripts/*.sh',
            'config.json'
        ]
    },
    entry_points={
        'console_scripts': [
            'claude-context=claude_context.cli:main',
            'ccb=claude_context.cli:main',  # Short alias
        ],
    },
    python_requires='>=3.7',
    install_requires=[
        'pytest>=6.0.0',
    ],
    extras_require={
        'dev': [
            'black',
            'flake8',
            'mypy',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)