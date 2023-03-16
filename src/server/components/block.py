import hashlib
import typing as tp
from datetime import datetime

from components import Serializable
from components.transaction import Transaction
from pydantic import Field


class Block(Serializable):
    index: int
    timestamp: datetime
    nonce: int
    previous_hash: str
    transactions: tp.List[Transaction] = Field(default_factory=list)
    current_hash: tp.Optional[str] = None

    @classmethod
    def calculate_hash(cls, block: "Block", include_hash: bool = False) -> None:
        data = block.json() if include_hash else block.json(exclude={"current_hash"})
        data = data.encode("utf-8")

        return hashlib.sha256(data).hexdigest()
