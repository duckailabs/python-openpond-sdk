from setuptools import find_packages, setup

setup(
    name="openpond-sdk",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.31.0",
        "typing-extensions>=4.7.1",
    ],
    author="OpenPond",
    author_email="sam@align.network",
    description="A Python SDK for interacting with the OpenPond P2P network",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/duckailabs/python-openpond-sdk",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
) 