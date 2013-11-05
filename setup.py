# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='pysemantic',
    version='0.0.1',
    description='PySemantic',
    long_description=readme,
    author='Mickey Petersen',
    author_email='mickey@masteringemacs.org',
    url='https://github.com/mickeynp/pysemantic',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

