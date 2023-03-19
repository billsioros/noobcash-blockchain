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
# Running the bootstrap node
python src/server/main.py -6
# Running the peer nodes
python3.6 src/server/main.py -6 --bootstrap http://\[2001:648:2ffe:501:cc00:13ff:fec5:f6db\]:5000 -n -2
# Gathering metrics
python src/client/main.py -n http://83.212.81.187:5000 metrics
