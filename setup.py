# -*- coding: utf-8 -*-

from setuptools import setup

import pynaut

# README.rst dynamically generated:
with open('README.rst', 'w') as f:
    f.write(pynaut.__doc__)

NAME = 'pynaut'

def read(file):
    with open(file, 'r') as f:
        return f.read().strip()

setup(
    name=NAME,
    version=read('VERSION'),
    description='A tool for recursively exploring arbitrary python objects.',
    long_description=read('README.rst'),
    author='Mike Burr',
    author_email='mburr@unintuitive.org',
    url='https://github.com/stnbu/{0}'.format(NAME),
    download_url='https://github.com/stnbu/{0}/archive/master.zip'.format(NAME),
    provides=[NAME],
    license='MIT',
    bugtrack_url='https://github.com/stnbu/{0}/issues'.format(NAME),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Debuggers',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    packages=[NAME, NAME+'.ui'],
    keywords=['introspection', 'debugging'],
    test_suite='nose.collector',
    test_requires=['nose'],
    entry_points={
        'console_scripts': [
            'pynaut_curses = pynaut.ui.curses:main',
        ],
        'gui_script': []},
)
