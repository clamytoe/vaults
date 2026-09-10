from vaults import __author__, __email__, __version__


def test_project_settings():
    assert __author__ == "Martin Uribe"
    assert __email__ == "clamytoe@gmail.com"
    assert __version__ == "0.1.1"
