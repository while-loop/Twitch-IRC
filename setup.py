#!/usr/bin/env python

from setuptools import setup

setup(
    name='twitchirc',
    version='0.0.1',
    description='Python library to interface with Twitch IRC (https://github.com/justintv/Twitch-API/blob/master/IRC.md)',
    author='Anthony Alves',
    author_email='cvballa3g0@gmail.com',
    url='https://github.com/while-loop/Twitch-IRC',
    packages=['twitchirc'],
    scripts=[],
    install_requires=["mock==2.0.0", "enum==0.4.6"],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
