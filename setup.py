#!/usr/bin/env python

from distutils.core import setup

setup(
    name='txwebtest',
    version='0.1.1',
    install_requires=["klein", "twisted"],
    py_modules=['txwebtest'],
    zip_safe=False,
)
