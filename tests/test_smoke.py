from importlib.metadata import version

from maily import __version__


def test_package_version():
    assert __version__ == version("maily")
