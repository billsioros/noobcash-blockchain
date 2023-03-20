import hashlib
import json
import typing as tp

from components import Serializable
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from pydantic import Field


class Transaction(Serializable):
    sender_address: str
    recipient_address: str
    amount: int
    id: tp.Optional[str] = None
    transaction_inputs: tp.List[str] = Field(default_factory=list)
    transaction_outputs: tp.List[tp.Tuple[str, str, str, int]] = Field(
        default_factory=list
    )
    signature: tp.Optional[str] = None

    @property
    def transaction_id(self) -> str:
        return self.id

    @classmethod
    def create_transaction(
        cls,
        sender_address: str,
        recipient_address: str,
        amount: int,
        transaction_inputs: tp.List["Transaction"],
        transaction_outputs: tp.List["Transaction"],
        private_key: str,
    ) -> "Transaction":
        transaction = cls(
            sender_address=sender_address,
            recipient_address=recipient_address,
            amount=amount,
            transaction_inputs=transaction_inputs,
            transaction_outputs=transaction_outputs,
        )
        transaction_data = {
            "sender_address": transaction.sender_address,
            "recipient_address": transaction.recipient_address,
            "amount": transaction.amount,
            "transaction_inputs": transaction.transaction_inputs,
            "transaction_outputs": transaction.transaction_outputs,
            "signature": transaction.signature,
        }

        transaction_string = json.dumps(transaction_data, sort_keys=True).encode(
            "utf-8"
        )

        transaction.id = hashlib.sha256(transaction_string).hexdigest()

        transaction.sign_transaction(private_key)

        return transaction

    def sign_transaction(self, private_key: str) -> None:
        # Load the private key
        key = RSA.import_key(bytes.fromhex(private_key))

        # Hash the transaction ID
        h = SHA256.new(self.id.encode("utf-8"))

        # Sign the hash with the private key
        signer = PKCS1_v1_5.new(key)
        signature = signer.sign(h)

        # Return the signature as a hex string
        self.signature = signature.hex()

    def verify_signature(self):
        # Load the public key of the sender
        key = RSA.import_key(bytes.fromhex(self.sender_address))

        # Hash the transaction ID
        h = SHA256.new(self.id.encode("utf-8"))

        # Verify the signature
        verifier = PKCS1_v1_5.new(key)

        return verifier.verify(h, bytes.fromhex(self.signature))
