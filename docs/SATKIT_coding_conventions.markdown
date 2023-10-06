# SATKIT Code Conventions

This document is a guideline, not a ruleset.

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

## Versioning

We use [SemVer](http://semver.org/) for versioning under the rules as
set out by [PEP 440](https://www.python.org/dev/peps/pep-0440/) with
the additional understanding that releases before 1.0 (i.e. current
releases at time of writing) have not been tested in any way.

For the versions available, see the [tags on this
repository](https://github.com/giuthas/satkit/tags).

## SATKIT's branches

SATKIT uses gitflow as the branching convention (until we have a reason for
doing something else). This means we have the following kinds of branches:

- `main` is the release branch. Any update here after 1.0 will get it's own
  version number and be considered a new version of SATKIT. See
  [Versioning](#versioning) above.
- `devel` is the main development branch. New features are added by branching
  from devel, working on the feature branch, and merging back to devel before
  creating a release branch that will be merged in to main to do the actual
  realease.
- Feature branches are used to develop a major feature. They may have
  subbranches as needed.
- Release branches are branched from `devel` when all of the features for a
  release have been implemented and merged back to `devel`. After creating the
  release branch, `main` is merged in to the release branch and any problems
  ironed out before creating the actual release by mergin into main. If any commits need to be made before merging into `main`, a merge back to `devel` needs to also be done.
- Hotfix branches can be branched off of any branch, but especially if branched
  from main they need to eventually be merged to both main *and* devel.
  Hotfixes are always small bug fixes never major features.
