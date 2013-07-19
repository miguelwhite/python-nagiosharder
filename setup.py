#!/usr/bin/env python2

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'


packages = [
    'nagiosharder'
]


requires = [
    'Logbook >= 0.4',
    'requests >= 0.13.3',
    'iniparse >= 0.4',
    'prettytable >= 0.6.1',
    'lxml==3.2.1',
    'cssselect==0.8'
]

setup(
    name='nagiosharder',
    version='0.2.5',
    description='lib and cli interface to nagios status.cgi',
    long_description=open('README.txt').read(),
    author='Alexandr Skurikhin',
    author_email='a@skurih.in',
    url='git://skurih.in/nagios-harder.git',
    scripts=['bin/nagiosharder'],
    packages=packages,
    package_data={'': ['LICENSE'] },
    install_requires=requires,
    license=open('LICENSE').read(),
)

del os.environ['PYTHONDONTWRITEBYTECODE']
