import hashlib
import typing as tp
from dataclasses import dataclass, field
from datetime import datetime

from components.transaction import Transaction
from loguru import logger


@dataclass
class Block(object):
    capacity: int
    index: int
    timestamp: datetime
    nonce: int
    current_hash: str
    previous_hash: str
    transactions: tp.List[Transaction] = field(default_factory=list)

    def validate_block(self, prev_block: "Block") -> bool:
        # Check if block's current hash is correct
        block_hash = hashlib.sha256(str(self.asdict()).encode()).hexdigest()
        if block_hash != self.current_hash:
            logger.info("Block hash is incorrect")
            return False

        # Check if block's previous hash is equal to hash of previous block
        if prev_block.current_hash != self.previous_hash:
            logger.info("Previous block hash is incorrect")
            return False

        return True
