import pytest
import py


@pytest.fixture(scope="function")
def datadir(request, tmpdir):
    """
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.

    Adapted from http://stackoverflow.com/questions/29627341
    """
    test_dir = py.path.local(request.module.__file__).new(ext='')
    try:
        for f in test_dir.listdir():
            f.copy(tmpdir)
    except:
        pass
    return tmpdir
