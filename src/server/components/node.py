import hashlib
import json
import threading
import typing as tp
from datetime import datetime

from components import Serializable
from components.block import Block
from components.blockchain import Blockchain
from components.transaction import Transaction
from components.wallet import Wallet
from core import http
from loguru import logger
from pydantic import Field


class Node(Serializable):
    ip: str
    port: int
    capacity: int
    difficulty: int
    n_nodes: int
    block_chain: Blockchain = Field(default_factory=Blockchain)
    id: tp.Optional[int] = None
    wallets: tp.Dict[str, Wallet] = Field(default_factory=dict)
    network: tp.List[str] = Field(default_factory=list)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        wallet = Wallet.generate_wallet()
        self.wallets[wallet.public_key] = wallet

    @property
    def wallet(self):
        return self.wallets[self.network[self.id][1]]

    @property
    def is_bootstrap(self) -> bool:
        return self.id == 0

    def broadcast_block(block, nodes):
        for node in nodes:
            url = f"http://{node}/add_block"
            response = http.post(url, block)
            if response.status_code != 200:
                logger.error("Failed to broadcast block to node {}", node)

    def create_transaction(
        self, sender_address: str, recipient_address: str, amount: int
    ) -> None:
        sender_wallet = self.wallets[sender_address]
        recipient_wallet = self.wallets[recipient_address]

        i, transaction_inputs = 0, []
        while amount > 0:
            id, _, _, transaction_amount = sender_wallet.utxos[i]

            if amount - transaction_amount > 0:
                transaction_inputs.append(id)
                amount -= transaction_amount
            elif amount - transaction_amount == 0:
                transaction_inputs.append(id)
                amount = 0
            else:
                transaction_inputs.append(id)
                amount = 0

        transaction = Transaction.create_transaction(
            sender_address,
            recipient_address,
            amount,
            transaction_inputs,
            [],
            sender_wallet.private_key,
        )

        change = recipient_wallet.balance - amount
        transaction.transaction_outputs = [
            (f"{self.id}:{transaction.id}", transaction.id, recipient_address, amount),
            (f"{self.id}:{transaction.id}", transaction.id, sender_address, change),
        ]

        self.block_chain.add_transaction(transaction)

        self.broadcast_transaction(transaction)

    def validate_transaction(self, Transaction: Transaction) -> bool:
        return True

    def broadcast_transaction(self, transaction: Transaction) -> None:
        logger.info("Broadcasting transaction {}", transaction.id)

        # Simulate broadcasting the transaction to all nodes
        for remote_address, _ in self.network[: self.id] + self.network[self.id + 1 :]:
            logger.info("Sending transaction {} to {}", transaction.id, remote_address)

            http.post(f"{remote_address}/transactions/broadcast", transaction)

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
        while (
            not hashlib.sha256(str(block).encode("utf-8"))
            .hexdigest()
            .startswith(target)
        ):
            block.nonce += 1

        # Add the miner's reward transaction to the list of transactions
        reward_tx = create_reward_transaction(miner_address)
        block.transactions.append(reward_tx)

        # Add the block to the blockchain and return the block hash
        blockchain.append(block)
        return hashlib.sha256(str(block).encode("utf-8")).hexdigest()

    def broadcast_block(block, nodes):
        for node in nodes:
            url = f"http://{node}/add_block"
            response = http.post(url, block)
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

    def resolve_conflict(self) -> None:
        """
        A function that resolves conflicts between nodes by selecting the longest blockchain.
        """

        longest_block_chain = self.block_chain

        # Find the longest chain from all the neighboring nodes
        max_length = len(longest_block_chain)
        for node in self.network:
            response = http.get(f"http://{node}/chain")
            payload = response.json()
            length, chain = payload["length"], payload["chain"]

            # Check if the length is longer and the chain is valid
            if length > max_length and self.validate_chain(chain):
                max_length = length
                longest_block_chain = chain

        # Replace the current blockchain with the new blockchain if it is longer and valid
        self.blockchain = longest_block_chain


class Bootstrap(Node):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        wallet = next(iter(self.wallets.values()))

        self.network.append((f"http://{self.ip}:{self.port}", wallet.public_key))

        transaction = Transaction.create_transaction(
            "0", wallet.public_key, 100 * self.n_nodes, [], [], wallet.private_key
        )

        transaction.transaction_outputs = [
            (
                f"{self.id}:{transaction.id}",
                transaction.id,
                wallet.public_key,
                100 * self.n_nodes,
            ),
            (f"{self.id}:{transaction.id}", transaction.id, "0", 0),
        ]

        wallet.utxos = [
            transaction.transaction_outputs[0],
        ]

        genesis_block = Block(
            capacity=self.capacity,
            index=0,
            timestamp=datetime.utcnow(),
            nonce=0,
            previous_hash=1,
            transactions=[transaction],
        )

        self.block_chain.append(genesis_block)

    def enroll(self, remote_address: str, public_key: str) -> int:
        logger.info("Registering {}", remote_address)

        self.network.append((remote_address, public_key))
        self.wallets[public_key] = Wallet(public_key=public_key, utxos=[])

        if len(self.network) == self.n_nodes:
            for remote_address, _ in self.network[1:]:
                logger.info("Enrolling {}", remote_address)

                http.post(
                    f"{remote_address}/nodes/enroll",
                    {
                        "network": json.dumps(self.network),
                        "block_chain": self.block_chain.json(),
                    },
                )

                self.create_transaction(self.wallet.public_key, public_key, 100)

        return len(self.network) - 1


class Peer(Node):
    bootstrap_address: tp.Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        threading.Thread(target=self.register).start()

    def register(self) -> None:
        assert self.id is None, f"Node has already been assigned id {self.id}"

        wallet = next(iter(self.wallets.values()))

        # Send my public key to the bootstrap node
        response = http.post(
            f"{self.bootstrap_address}/nodes/register",
            {"port": self.port, "public_key": wallet.public_key},
        )
        payload = response.json()

        self.id = payload["id"]

        logger.info("Received id: {}", self.id)
