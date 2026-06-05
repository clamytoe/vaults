from os import environ

from dotenv import load_dotenv

from vaults import __author__, __email__, __version__


def test_project_settings():
    assert __author__ == "Martin Uribe"
    assert __email__ == "clamytoe@gmail.com"
    assert __version__ == "0.1.0"


def test_env():
    load_dotenv()
    assert environ.get("TEST_VALUE") == "clamytoe"
