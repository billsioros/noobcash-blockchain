# Noobcash Blockchain

- [Noobcash Blockchain](#noobcash-blockchain)
  - [Setting up the project](#setting-up-the-project)

## Setting up the project

First of all install python 3.6(.13). This can be achieved using [`pyenv`](https://github.com/pyenv/pyenv)

```shell
pyenv install 3.6.13
pyenv local 3.6.13
```

Afterward, install [`virtualenv`](https://virtualenv.pypa.io/en/latest/) as follows

```shell
python -m pip install virtualenv
```

Finally, create a virtual Python environment using `virtualenv`, activate it and install the required packages as follows

```shell
python -m virtualenv .env
source .env/bin/activate
python -m pip install -r requirements.txt
```
