#!/usr/bin/env python

from setuptools import setup
from time import time
import sys
import os

BUILDTIME_TEMPLATE = 'BUILDTIME'

requires=[]

def make_buildtime_file():
    with open(BUILDTIME_TEMPLATE, 'w') as f:
        now = time()
        f.write(str(now))

def get_version():
    if not os.path.exists(BUILDTIME_TEMPLATE):
        make_buildtime_file()
    buildtime = open(BUILDTIME_TEMPLATE, 'r').read()
    buildtime = float(buildtime)
    version = '0.1.{0}'.format(int(buildtime/60.0))
    return version

name='pynaut'

setup(name=name,
    version=get_version(),
    description='A Python Object Explorer',
    long_description=open('README.md', 'r').read(),
    author='Mike Burr',
    author_email='mburr@unintuitive.org',
    license='LGPL',
    install_requires=requires,
    requires=requires,
    url='https://github.com/stnbu/pynaut',
    classifiers=[],
    packages=[
        'pynaut',
    ],
)


