from setuptools import setup, find_packages
import os

# Get absolute path
here = os.path.abspath(os.path.dirname(__file__))

# Read version from __version__.py
version = {}
with open(os.path.join(here, "flaredantic", "__version__.py")) as f:
    exec(f.read(), version)

# Read requirements from requirements.txt
with open(os.path.join(here, "requirements.txt"), encoding='utf-8') as f:
    requirements = [line.strip() for line in f.readlines()]

setup(
    name="flaredantic",
    version=version["__version__"],
    packages=find_packages(),
    install_requires=requirements,
    author="linuztx",
    author_email="linuztx@gmail.com",
    description="A Python library for creating free Cloudflare tunnels with ease",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/linuztx/flaredantic",
    license="Apache License 2.0", 
    classifiers=[
        "Operating System :: OS Independent",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.6",
    keywords="cloudflare tunnel development networking proxy webhook",
    project_urls={
        "Bug Reports": "https://github.com/linuztx/flaredantic/issues",
        "Source": "https://github.com/linuztx/flaredantic",
    },
    entry_points={
        'console_scripts': [
            'flare=flaredantic.cli:main',
        ],
    },
)
