import typing as tp

from components import Serializable
from components.block import Block
from components.transaction import Transaction
from pydantic import Field


class Blockchain(Serializable):
    blocks: tp.List[Block] = Field(default_factory=list)

    def append(self, block: Block) -> None:
        self.blocks.append(block)

    def add_transaction(self, transaction: Transaction) -> None:
        self.blocks[-1].transactions.append(transaction)

    def __len__(self) -> int:
        return len(self.blocks)
