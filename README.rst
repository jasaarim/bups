Bups (back-ups)
===============

A simple command-line back-up utility that copies files based on their
modification times.  There are probably many tools that achieve
exactly the same this, but at a time writing this seemed almost as
trivial as finding and learning a write tool.

Initially this started as an exercise for traversing a tree structure
with recursive function calls.  Afterwards I decided to make a full
package from it.

The program has been tested only on Linux using Python 3.  To install
type::

    python setup.py install

After that the usage is shown by typing::

    pubs --help
