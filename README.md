# Noobcash Blockchain

- [Noobcash Blockchain](#noobcash-blockchain)
  - [Setting up the project](#setting-up-the-project)
    - [Setting up pre-commit hooks (Development Only)](#setting-up-pre-commit-hooks-development-only)

Blockchain architecture is a distributed ledger technology that allows for secure and decentralized transactions without the need for a central authority. The blockchain consists of a network of nodes, each of which maintains a copy of the ledger, and transactions are validated through a consensus mechanism. One of the most common consensus mechanisms used in blockchain technology is called proof-of-work (PoW). In a PoW system, nodes called "miners" compete to solve a cryptographic puzzle that requires significant computational power. The first miner to solve the puzzle and validate a block of transactions is rewarded with new cryptocurrency coins and transaction fees. Once a block is validated, it is added to the blockchain and distributed to all nodes in the network. The other nodes then verify the new block and add it to their own copies of the ledger. This process creates a decentralized and secure system in which transactions cannot be altered or deleted without the consensus of the entire network.

In our case, we explore a simplistic blockchain implementation approach wherein a predetermined node, referred to as *Bootstrap* node, is responsible for:

- generating the genesis block. The genesis block refers to the first block that is appended to the blockchain. It is the only block that is not validated before being added to the blockchain and contains a single transaction, via which 100 x n coins are transferred to the bootstrap node, where $n$ refers to the number of nodes participating in the system.
- enrolling every other (*Peer*) node into the system. The term *"enrolling"* refers to the process of exchanging information regarding the distributed system with the peer nodes. To be more specific, a peer node contacts the bootstrap node in order to make itself known to it. Having done so, the bootstrap assigns the peer node at hand a new system id. When all peer nodes have successfully contacted the bootstrap node, the bootstrap node broadcasts the complete node network, the current state of the blockchain (which only contains the genesis block at this time) as well as the virtual addresses of all nodes participating in the network which are used in the context of a transaction.
- distributing an equal fixed amount of coins to each node. This is achieved by creating n - 1 individual transactions of 100 coins targeting each of the peer nodes, where $n$ refers to the number of nodes participating in the system. Each transaction is carried out in a distributed fashion, meaning that it is broadcasted to and validated by each and every node.

Having done so the bootstrap node then behaves mostly identically to a *Peer* node. Whenever a new transaction is created, regardless of its node of origin, it is broadcasted to and validated by each and every node. When a certain number of transactions is reached the mining process begins. More specifically, each node tries out different nonce values for the block at hand, and whichever is able to validate the block first, broadcasts it to all other nodes. The block is then validated by each receiving node and added to their respective blockchain. Whenever a node fails to validate the incoming block, consensus is reached by retrieving the blockchain states of all other nodes and maintaining the one with the greatest length.

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

Create a virtual Python environment using `virtualenv` and activate it as follows

```shell
python -m virtualenv .env
source .env/bin/activate
```

Finally, clone the project and install the required dependencies:

```shell
git clone https://github.com/billsioros/noobcash-blockchain
python -m pip install -r requirements.txt
```

### Setting up pre-commit hooks (Development Only)

Having installed all necessary dependencies, run the following so that you install all the necessary pre-commit hooks:

```shell
pre-commit install --install-hooks
```
