"""
run these tests with `pytest tests/test_something.py` or `pytest tests` or simply `pytest`
pytest will look for all files starting with "test_" and run all functions
within this file. For basic example of tests you can look at our workshop
https://github.com/rl-institut/workshop/tree/master/test-driven-development.
Otherwise https://docs.pytest.org/en/latest/ and https://docs.python.org/3/library/unittest.html
are also good support.
"""
import src.simulation


# this function will not run as a test as its name does not start by "test_"
def addition(a, b):
    return a + b


# each test is described in a function, the function must start with "test_"
# something has to be asserted within the function
def test_addition():
    assert addition(2, 2) == 4
