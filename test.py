import sys
import unittest
import doctest

# all of the testable modules
# when another module needs to be incorporated into tests
# they should be added here

import cogs.basic
import cogs.courseInfo
import cogs.number_utils
import cogs.gpa
import cogs.manpage
import cogs.markov
import cogs.hyphen

test_modules = [
    cogs.basic,
    cogs.courseInfo,
    cogs.number_utils,
    cogs.gpa,
    cogs.manpage,
    cogs.markov,
    cogs.hyphen
]

def load_tests(tests):
    # add each of the test modules
    for mod in test_modules:
        tests.addTests(doctest.DocTestSuite(mod))
    return tests

if __name__ == '__main__':
    """
    runs the tests
    
    """
    tests = unittest.TestSuite()
    test = load_tests(tests)
    runner = unittest.TextTestRunner()
    # get the exit code and return when failed
    ret = not runner.run(tests).wasSuccessful()
    sys.exit(ret)


