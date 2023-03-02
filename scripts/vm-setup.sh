# Installing general dependencies
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install gcc make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# Installing pyenv
git clone https://github.com/pyenv/pyenv.git ~/.pyenv
cd ~/.pyenv && src/configure && make -C src
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile
echo 'eval "$(pyenv init -)"' >> ~/.profile
exec "$SHELL"
cd ~

# Installing Python 3.6.13
pyenv install 3.6.13
pyenv global 3.6.13

# Configure git
git config --global user.email "billsioros97@gmail.com"
git config --global user.name "billsioros"

# Set up the project
git clone https://github.com/billsioros/noobcash-blockchain
cd noobcash-blockchain/
python -m pip install -r requirements.txt
