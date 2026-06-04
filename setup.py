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
        "cryptography",
        "ddgs",
        "requests",
        "beautifulsoup4",
        "pyautogui",
        "schedule",
        "plyer",
        "watchdog",
        "pyngrok"
    ],
    entry_points={
        "console_scripts": [
            "tga=tagaura.cli:main",
        ],
    },
)
