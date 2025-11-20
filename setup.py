"""Setup script for Apollo ElevenLabs Call Orchestrator."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="apollo-elevenlabs-orchestrator",
    version="0.1.0",
    description="Call agent orchestrator that integrates Apollo.io contacts with ElevenLabs AI calling",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Oskar Freye",
    author_email="oskar@freye.tech",
    url="https://github.com/execute008/apollo11",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "PyYAML>=6.0.1",
        "aiohttp>=3.9.0",
        "colorlog>=6.8.0",
        "tenacity>=8.2.3",
        "click>=8.1.7",
        "rich>=13.7.0",
        "textual>=0.47.0",
        "openai>=1.10.0",
        "anthropic>=0.18.0",
        "phonenumbers>=8.13.0",
        "requests-cache>=1.1.1",
        "psutil>=5.9.0",
    ],
    extras_require={
        "dev": [
            "textual-dev>=1.2.0",
            "pytest>=7.4.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "apollo-call=src.main:main",
            "apollo-tui=src.tui_main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Communications :: Telephony",
        "Topic :: Office/Business",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
