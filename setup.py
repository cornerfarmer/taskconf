from setuptools import setup

setup(name='taskconf',
      version='0.9',
      url='http://github.com/domin1101/taskconf',
      author='Dominik Winkelbauer',
      packages=['taskconf'],
      test_suite="tests",
      tests_require=["pytest"])