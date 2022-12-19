# Setting SATKIT up for Development

The most important steps for getting SATKIT installed in development mode are:

- Get a copy of the source code:
  - Either [fork and clone the repository](#fork-and-clone-the-repository) it to the local system
  - or if you do not intend to publish your changes, just [clone directly from the SATKIT main](#clone-directly-from-the-satkit-main).
- [Create the conda environments](#create-the-conda-environments).
- [Install SATKIT in development mode](#install-satkit-in-development-mode).

Other topics covered by this guide:

- [Rebuild and activate conda environment after updating the environment](#rebuild-and-activate-conda-environment-after-updating-the-environment).

## Fork and clone the repository

First, fork the repository from [https://github.com/giuthas/satkit](https://github.com/giuthas/satkit).

Second, clone the repository to your local system.

Third, if not automatically done, setup the original repository as your upstream repo:

```bash
git remote add upstream https://github.com/giuthas/satkit
git fetch upstream
git merge upstream/main main
```

Here's what this does in practice:

![forking SATKIT](forking_satkit.drawio.png)

## Clone directly from the SATKIT main

In a directory that you would like the clone to live in, run the following command optionally giving a name for the directory SATKIT will be cloned to.

```bash
git clone https://github.com/giuthas/satkit [optional directory]
```

## Create the conda environments

Once you have a copy of SATKIT's source code, run these commands on the command line:

```bash
cd [satkit root]
mamba env create -f satkit_stable_conda_env.yaml
mamba env create -f satkit_devel_conda_env.yaml
```

And to actually use the latter:

```bash
conda activate satkit-devel
```

## Install SATKIT in development mode

This should work in [the usual way](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/#working-in-development-mode) for Python packages by just running `pip install -e .` in the root directory of SATKIT -- NOT the `satkit` directory inside the package, but the root directory of the repository.

This will enable use of SATKIT as a library as if it were a regularly installed Python package, while waht actually gets used is the live code base in the local repository. **This needs to be done separately for each Python conda/virtual environment in use.**

## Other topics

### Rebuild and activate conda environment after updating the environment

After either downloading a newer version or making local changes, run these commands on the command line:

```bash
conda activate base
conda env remove -n satkit-devel
mamba env create -f satkit_devel_conda_env.yaml
conda activate satkit-devel
```

Substitute `satkit-stable` for `satkit-devel` and `satkit_stable_conda_env.yaml` for `satkit_devel_conda_env.yaml` to update the stable environment.
