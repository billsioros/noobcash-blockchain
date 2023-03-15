import typing as tp

from components import Serializable
from components.block import Block
from pydantic import Field


class Blockchain(Serializable):
    blocks: tp.List[Block] = Field(default_factory=list)
