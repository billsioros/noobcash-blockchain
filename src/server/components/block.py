import hashlib
import typing as tp
from datetime import datetime

from components import Serializable
from components.transaction import Transaction
from loguru import logger
from pydantic import Field


class Block(Serializable):
    index: int
    timestamp: datetime
    nonce: int
    previous_hash: str
    current_hash: tp.Optional[str] = None
    transactions: tp.List[Transaction] = Field(default_factory=list)

    @classmethod
    def calculate_hash(cls, block: "Block") -> None:
        return hashlib.sha256(block.json().encode("utf-8")).hexdigest()
