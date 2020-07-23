#!/usr/bin/env python

import io
import os
from setuptools import setup, find_packages


def read(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with io.open(filepath, mode='r', encoding='utf-8') as f:
        return f.read()


setup(
    name="watchfor",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: Polish",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    description="CLI application for monitoring online services",
    license="MIT",
    long_description=read('README.md'),
    url="https://github.com/tru-software/watchfor",
    project_urls={
        "Documentation": "CLI application for monitoring online services",
        "Source Code": "https://github.com/tru-software/watchfor",
    },

    author="TRU SOFTWARE",
    author_email="at@tru.pl",

    setup_requires=["setuptools_scm"],
    use_scm_version=True,

    # packages=find_packages(),
    install_requires=read('requirements.txt').splitlines(),

    entry_points={
        'console_scripts': [
            'watchfor = watchfor:main',
        ]
    },
    packages=["watchfor"]
)
