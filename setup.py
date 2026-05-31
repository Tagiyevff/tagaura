from setuptools import setup, find_packages

setup(
    name="tagaura",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click",
        "rich",
        "questionary",
        "litellm",
        "psutil",
        "cryptography"
    ],
    entry_points={
        "console_scripts": [
            "tga=tagaura.cli:main",
        ],
    },
)
