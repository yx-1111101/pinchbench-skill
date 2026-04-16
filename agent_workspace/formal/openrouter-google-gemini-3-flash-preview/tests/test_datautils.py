from datautils import __doc__


def test_package_importable():
    assert __doc__ is not None
