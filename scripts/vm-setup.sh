# Setup script
# Installing general dependencies
sudo apt-get update
sudo apt-get -y upgrade
sudo apt-get -y install gcc make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# Install python
wget https://www.python.org/ftp/python/3.6.13/Python-3.6.13.tar.xz
tar xvf Python-3.6.13.tar.xz
cd Python-3.6.13/ && ./configure && sudo make altinstall

# Install dependencies
python3.6 -m pip install -r requirements.txt

# Useful commands
# Copy project from bootstrap to peer
scp -6 -r /home/user/noobcash-blockchain/  user@\[snf-35093.ok-kno.grnetcloud.net\]:/home/user/
# Connect to peer
sshpass -p '<PASSWORD>' ssh user@snf-35093.ok-kno.grnetcloud.net
