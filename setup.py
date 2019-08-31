from setuptools import setup

PACKAGE = "logsql"
VERSION = "0.0.0"

setup(
    name=PACKAGE,
    version=VERSION,
    packages=["logsql"],
    install_requires=[
        "docker",
        "sqlalchemy",
    ],
    extras_require={
        "dev": [
            "addict",
            "coverage",
            "pylint",
            "pytest",
            "pytest-cov",
            "pytest-env",
            "pytest-dotenv",
            "pytest-mock",
            "requests",
            "flake8",
            "flake8-quotes",
            "sphinx",
            "sphinxcontrib-napoleon",
        ],
    }
)
