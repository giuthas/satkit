# Setting SATKIT up for Development

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

## Rebuild and activate after updating the environment

After either downloading a newer version or making local changes, run these commands on the command line:

```bash
conda activate base
conda env remove -n satkit-devel
mamba env create -f satkit_devel_conda_env.yaml
conda activate satkit-devel
```

Substitute `satkit-stable` for `satkit-devel` and `satkit_stable_conda_env.yaml` for `satkit_devel_conda_env.yaml` to update the stable environment.
