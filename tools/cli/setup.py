"""Setup configuration for Prometheus CLI."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="prometheus-cli",
    version="0.1.0",
    author="Prometheus Team",
    author_email="team@prometheus.dev",
    description="A command-line tool for Prometheus project initialization and management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AlessioPili-KT/Prometheus",
    project_urls={
        "Bug Tracker": "https://github.com/AlessioPili-KT/Prometheus/issues",
        "Source Code": "https://github.com/AlessioPili-KT/Prometheus/tree/main/tools/cli",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=5.0",
            "mypy>=0.990",
        ],
    },
    entry_points={
        "console_scripts": [
            "prometheus=prometheus.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    keywords="prometheus cli project initialization management",
)
