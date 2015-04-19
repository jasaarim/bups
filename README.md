Bups (Back-ups)
===============

A simple command-line back-up tool that creates and updates mirrors for
directories in a local filesystem.  Mirror directories are updated
based on modification times of source files.  Files that exist in mirrors
but not in source are also removed.

The program doesn't probably do anything that couldn't be achieved
with, e.g., rsync.  Initially the program was written because it
offered a nice exercise in recursive loops.

Installation
============

The program has been tested only on Linux using Python3.4.  Other Python
versions may or may not work.  To install you need to have setuptools
installed in your Python version.  You can run::

    python3 setup.py install

and this will create a command-line entry point.  Type::

    pubs --help

to see the usage.