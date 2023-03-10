import hashlib
import json
import threading
import typing as tp
from dataclasses import dataclass, field

import requests
from components.block import Block
from loguru import logger


@dataclass()
class Node(object):
    ip: str
    port: int
    difficulty: int
    n_nodes: int
    id: tp.Optional[int] = None
    network: tp.List[str] = field(default_factory=list)
    block_chain: tp.List[Block] = field(default_factory=list)

    @property
    def is_bootstrap(self) -> bool:
        return self.id == 0

    def broadcast_block(block, nodes):
        for node in nodes:
            url = f"http://{node}/add_block"
            response = requests.post(url, json=block.__dict__)
            if response.status_code != 200:
                logger.error("Failed to broadcast block to node {}", node)

    def broadcast_transaction(transaction, node_addresses):
        # Simulate broadcasting the transaction to all nodes
        for node_address in node_addresses:
            # Here, we would actually send the transaction to the node using a network protocol
            logger.info(
                "Transaction {} broadcasted to node {}",
                transaction.transaction_id,
                node_address,
            )

    def wallet_balance(wallet_address):
        """
        Calculate the balance of a wallet by adding all unspent transaction outputs that
        have the wallet_address as the recipient.
        """
        balance = 0
        for tx_output in unspent_tx_outputs:
            if tx_output.recipient == wallet_address:
                balance += tx_output.amount
        return balance

    def mine_block(transactions, previous_block_hash, difficulty, miner_address):
        """
        Mine a new block by finding a nonce that makes the block hash start with a certain
        number of zeroes determined by the difficulty constant.
        """
        # Create a new block with the given transactions and previous block hash
        block = Block(transactions, previous_block_hash)
        block.nonce = 0

        # Keep trying different values of the nonce until the block hash starts with
        # the required number of zeroes
        target = "0" * difficulty
        while not hashlib.sha256(str(block).encode()).hexdigest().startswith(target):
            block.nonce += 1

        # Add the miner's reward transaction to the list of transactions
        reward_tx = create_reward_transaction(miner_address)
        block.transactions.append(reward_tx)

        # Add the block to the blockchain and return the block hash
        blockchain.append(block)
        return hashlib.sha256(str(block).encode()).hexdigest()

    def broadcast_block(block, nodes):
        for node in nodes:
            url = f"http://{node}/add_block"
            response = requests.post(url, json=block.__dict__)
            if response.status_code != 200:
                logger.error("Failed to broadcast block to node {}", node)

    def validate_chain(blockchain):
        """
        Validates the correctness of the blockchain received from the bootstrap node.

        Args:
            blockchain (list): The blockchain to validate.

        Returns:
            bool: True if the blockchain is valid, False otherwise.
        """
        # Check if the genesis block is correct
        if blockchain[0].hash != genesis_block.hash:
            return False

        # Check each block in the chain
        for i in range(1, len(blockchain)):
            current_block = blockchain[i]
            previous_block = blockchain[i - 1]

            # Verify current hash
            if current_block.hash != current_block.calculate_hash():
                return False

            # Verify previous hash
            if current_block.previous_hash != previous_block.hash:
                return False

        # If all blocks are valid, return True
        return True

    def resolve_conflict(self):
        """
        A function that resolves conflicts between nodes by selecting the longest blockchain.
        """
        global blockchain

        neighbors = get_neighbors()
        new_chain = None

        # Find the longest chain from all the neighboring nodes
        max_length = len(blockchain)
        for node in neighbors:
            response = requests.get(f"http://{node}/chain")
            length = response.json()["length"]
            chain = response.json()["chain"]

            # Check if the length is longer and the chain is valid
            if length > max_length and self.validate_chain(chain):
                max_length = length
                new_chain = chain

        # Replace the current blockchain with the new blockchain if it is longer and valid
        if new_chain:
            blockchain = new_chain
            return True

        return False


@dataclass
class Bootstrap(Node):
    def add_to_ring(self, address: str) -> int:
        logger.info("Broadcasting the network")

        self.network.append(address)
        if len(self.network) == self.n_nodes:
            logger.info("Sending the network to {}", address)

            requests.post(
                f"{address}/nodes/routing-table",
                json={"network": json.dumps(self.network)},
            )

        return len(self.network)


@dataclass
class Peer(Node):
    bootstrap_address: tp.Optional[str] = None

    def __post_init__(self):
        threading.Thread(target=self.register).start()

    def register(self) -> None:
        assert self.id is None, f"Node has already been assigned id {self.id}"

        # Send my public key to the bootstrap node
        response = requests.post(
            f"{self.bootstrap_address}/nodes/register",
            json={"port": self.port, "address": "node.wallet.address"},
        )
        payload = response.json()

        self.id = payload["id"]

        logger.info("Received id: {}", self.id)

    def set_ring(self, network: tp.List[str]) -> None:
        self.network = network
