from setuptools import setup, find_packages
import os

# Read version from __version__.py
version = {}
with open(os.path.join("flaredantic", "__version__.py")) as f:
    exec(f.read(), version)

setup(
    name="flaredantic",
    version=version["__version__"],
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0,<3.0.0",
        "tqdm>=4.50.0,<5.0.0",
    ],
    author="linuztx",
    author_email="linuztx@gmail.com",
    description="A Python library for creating free Cloudflare tunnels with ease",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/linuztx/flaredantic",
    classifiers=[
        "Operating System :: OS Independent",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
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
    python_requires=">=3.7",
    keywords="cloudflare tunnel development networking proxy",
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
