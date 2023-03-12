import typing as tp

from components import Serializable
from Crypto.PublicKey import RSA
from pydantic import Field


class Wallet(Serializable):
    public_key: tp.Optional[str] = None
    private_key: tp.Optional[str] = None
    utxos: tp.List[tp.Tuple[str, str, str, int]] = Field(default_factory=list)

    @classmethod
    def generate_wallet(cls) -> "Wallet":
        # Generate a new RSA key pair
        key_pair = RSA.generate(2048)

        # Extract the public and private keys
        private_key = key_pair.export_key()
        public_key = key_pair.publickey().export_key()

        # Return the keys as hex-encoded strings
        return Wallet(public_key=public_key.hex(), private_key=private_key.hex())

    @property
    def balance(self) -> int:
        return self.wallet_balance()

    def wallet_balance(self):
        """
        Calculate the balance of a wallet by adding all unspent transaction outputs that
        have the wallet_address as the recipient.
        """
        balance = 0
        for _, _, _, amount in self.utxos:
            balance += amount
        return balance
