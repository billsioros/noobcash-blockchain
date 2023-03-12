import hashlib
import typing as tp
from datetime import datetime

from components import Serializable
from components.transaction import Transaction
from loguru import logger
from pydantic import Field


class Block(Serializable):
    capacity: int
    index: int
    timestamp: datetime
    nonce: int
    previous_hash: str
    transactions: tp.List[Transaction] = Field(default_factory=list)

    def validate_block(self, prev_block: "Block") -> bool:
        # Check if block's current hash is correct
        block_hash = hashlib.sha256(self.json()).encode("utf-8").hexdigest()
        if block_hash != self.current_hash:
            logger.info("Block hash is incorrect")
            return False

        # Check if block's previous hash is equal to hash of previous block
        if prev_block.current_hash != self.previous_hash:
            logger.info("Previous block hash is incorrect")
            return False

        return True

    @property
    def current_hash(self) -> None:
        return hashlib.sha256(self.json()).encode("utf-8").hexdigest()
