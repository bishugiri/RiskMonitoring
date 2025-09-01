#!/usr/bin/env python3
"""
Setup script for the Risk Monitor package
"""

from setuptools import setup, find_packages
import os

# Read the requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Read the README file for the long description
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="risk_monitor",
    version="1.0.0",
    description="A tool for monitoring financial risks through news analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Risk Monitor Team",
    author_email="info@riskmonitor.example",
    url="https://github.com/example/risk-monitor",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "risk-monitor-refresh=risk_monitor.scripts.run_data_refresh:main",
            "risk-monitor-app=risk_monitor.scripts.run_app:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Office/Business :: Financial",
    ],
)