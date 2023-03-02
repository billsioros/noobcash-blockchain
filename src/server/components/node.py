import json
import threading
import typing as tp
from dataclasses import dataclass, field

import requests
from loguru import logger


@dataclass()
class Node(object):
    ip: str
    port: int
    difficulty: int
    n_nodes: int
    id: tp.Optional[int] = None
    ring: tp.List[str] = field(default_factory=list)

    @property
    def is_bootstrap(self) -> bool:
        return self.id == 0


@dataclass
class Bootstrap(Node):
    def add_to_ring(self, address: str) -> int:
        logger.info("Broadcasting the ring")

        self.ring.append(address)
        if len(self.ring) == self.n_nodes:
            logger.info("Sending the ring to {}", address)

            requests.post(
                f"{address}/nodes/routing-table",
                json={"ring": json.dumps(self.ring)},
            )

        return len(self.ring)


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

    def set_ring(self, ring: tp.List[str]) -> None:
        self.ring = ring
