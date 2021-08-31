#!/usr/bin/env python
from setuptools import setup

setup(
    name="tap-amplitude-api",
    version="0.1.8",
    description="Singer.io tap for extracting date from amplitude via API",
    author="FNM, ashalitkin",
    url="https://github.com/fridgenomore/singer-tap-amplitude ",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_amplitude"],
    install_requires=[
        # NB: Pin these to a more specific version for tap reliability
        "singer-python",
        "requests",
    ],
    entry_points="""
    [console_scripts]
    tap-amplitude-api=tap_amplitude:main
    """,
    packages=["tap_amplitude"],
    package_data = {
        "schemas": ["tap_amplitude/schemas/*.json"]
    },
    include_package_data=True,
)
