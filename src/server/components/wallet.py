import typing as tp
from dataclasses import dataclass

from Crypto.PublicKey import RSA


@dataclass
class Wallet(object):
    public_key: tp.Optional[str] = None
    private_key: tp.Optional[str] = None

    @classmethod
    def generate_wallet(cls) -> tp.Tuple[str, str]:
        # Generate a new RSA key pair
        key_pair = RSA.generate(2048)

        # Extract the public and private keys
        private_key = key_pair.export_key()
        public_key = key_pair.publickey().export_key()

        # Return the keys as hex-encoded strings
        return private_key.hex(), public_key.hex()
