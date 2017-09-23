#!/usr/bin/env python

from setuptools import setup

setup(

    name="APyTumblr",
    version="0.0.7",
    description="An AsyncIO Python API v2 wrapper for Tumblr",
    author="henry232323",
    author_email="henry@rhodochrosite.xyz",
    url="https://github.com/henry232323/pytumblr",
    packages = ['pytumblr'],
    license = "LICENSE",

    test_suite='nose.collector',

    install_requires = [
        'aioauth-client',
    ],

    tests_require=[
        'nose',
        'nose-cov',
        'mock'
    ]

)
