# Noobcash Blockchain

- [Noobcash Blockchain](#noobcash-blockchain)
  - [Setting up the project](#setting-up-the-project)
    - [(Development Only) Setting up pre-commit hooks](#development-only-setting-up-pre-commit-hooks)

## Setting up the project

First of all install python 3.6(.13). This can be achieved using [`pyenv`](https://github.com/pyenv/pyenv)

```shell
# In case you do not have pyenv installed
git clone https://github.com/pyenv/pyenv.git ~/.pyenv
cd ~/.pyenv && src/configure && make -C src
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile
echo 'eval "$(pyenv init -)"' >> ~/.profile
exec "$SHELL"

# Actual installation of python 3.6
pyenv install 3.6.13
pyenv local 3.6.13
```

Afterward, install [`virtualenv`](https://virtualenv.pypa.io/en/latest/) as follows

```shell
python -m pip install virtualenv
```

Create a virtual Python environment using `virtualenv`, activate it and install the required packages as follows

```shell
python -m virtualenv .env
source .env/bin/activate
```

Finally, clone the project and install the required dependencies:

```shell
git clone https://github.com/billsioros/noobcash-blockchain
python -m pip install -r requirements.txt
```

### (Development Only) Setting up pre-commit hooks

Having installed all necessary dependencies, run the following so that you install all the necessary pre-commit hooks:

```shell
pre-commit install --install-hooks
```
