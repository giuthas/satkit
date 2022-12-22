# SATKIT Code Conventions

This document is a guideline, not a ruleset, and really a thing Pertti wrote for
himself to be able to remember these things.

First things first: write in good pythonic style.

- [PEP 8](https://www.python.org/dev/peps/pep-0008/) outlines the general style.
  - Most of these guidelines can be followed automatically by using the [autopep8](https://pypi.org/project/autopep8/) and pylint packages to format code.
- [PEP 257](https://www.python.org/dev/peps/pep-0257/) talks about conventions for docstrings. In addition we might do the following:
  - Consider what will look good once the docs are compiled.
  - If we are using pdoc, repeating the same thing for a class docstring and the
      constructor is not a good idea. Instead, write general description in the
      class docstring and describe arguments and such in the constructor's
      docstring. This way they'll also make sense when reading the source.
  - Besides docstrings write other comments too.

Also follow the [Zen of Python](https://www.python.org/dev/peps/pep-0020/) with
the following additions:

- Getting it done is better than making it perfect (because getting it perfect
  won't happen).
- A module is the unit of reuse. Ideally, a module should do something that gets
  used time and time again, but it is good enough if it does something which has a clear and self contained purpose. Prefer splitting to smaller modules over piles of unrelated code.

## Packages and modules

In Python a module is -- [roughly
speaking](https://docs.python.org/3/reference/import.html#packages) -- any .py
file and a regular package is a directory that contains a `__init__.py` file and
possibly some other `.py` files. In SATKIT `__init__.py` files are used for two
purposes: Defineing the public API of the module and running any initialisation
that is needed. For an example have a look at `satkit/__init__.py`.
