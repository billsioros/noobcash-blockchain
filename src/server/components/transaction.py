import hashlib
import json
import typing as tp
from dataclasses import dataclass, field

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


@dataclass
class Transaction(object):
    sender_address: str
    receiver_address: str
    amount: float
    transaction_id: str
    transaction_inputs: tp.List["Transaction"] = field(default_factory=list)
    transaction_outputs: tp.List["Transaction"] = field(default_factory=list)
    signature: tp.Optional[str] = None

    def __post_init__(self) -> None:
        transaction_data = {
            "sender_address": self.sender_address,
            "receiver_address": self.receiver_address,
            "amount": self.amount,
            "transaction_inputs": self.transaction_inputs,
            "transaction_outputs": self.transaction_outputs,
            "signature": self.signature,
        }

        transaction_string = json.dumps(transaction_data, sort_keys=True).encode(
            "utf-8"
        )

        self.transaction_id = hashlib.sha256(transaction_string).hexdigest()

    @classmethod
    def create_transaction(
        cls,
        sender_address: str,
        receiver_address: str,
        amount: float,
        transaction_inputs: tp.List["Transaction"],
        transaction_outputs: tp.List["Transaction"],
        private_key: str,
    ) -> "Transaction":
        transaction = Transaction(
            sender_address,
            receiver_address,
            amount,
            transaction_inputs,
            transaction_outputs,
        )
        transaction.signature = cls.sign_transaction(
            transaction.transaction_id, private_key
        )

        return transaction

    @classmethod
    def sign_transaction(cls, transaction_id: str, private_key: str) -> str:
        # Load the private key
        key = RSA.import_key(private_key)

        # Hash the transaction ID
        h = SHA256.new(transaction_id.encode("utf-8"))

        # Sign the hash with the private key
        signer = PKCS1_v1_5.new(key)
        signature = signer.sign(h)

        # Return the signature as a hex string
        return signature.hex()

    @classmethod
    def verify_signature(cls, transaction):
        # Load the public key of the sender
        key = RSA.import_key(transaction.sender_address)

        # Hash the transaction ID
        h = SHA256.new(transaction.transaction_id.encode("utf-8"))

        # Verify the signature
        verifier = PKCS1_v1_5.new(key)

        return verifier.verify(h, bytes.fromhex(transaction.signature))

    @classmethod
    def validate_transaction(
        cls, transaction: "Transaction", unspent_tx_outputs: tp.List["Transaction"]
    ) -> bool:
        # Verify transaction signature
        if not cls.verify_signature(transaction):
            return False

        # Check if transaction inputs are valid unspent transactions
        inputs_sum = 0
        for tx_input in transaction["transaction_inputs"]:
            tx_output = unspent_tx_outputs.get(tx_input["previousOutputID"])
            if not tx_output:
                return False
            if tx_output["recipient"] != transaction["sender_address"]:
                return False
            inputs_sum += tx_output["amount"]

        # Check that transaction inputs cover the amount being sent
        if inputs_sum < transaction["amount"]:
            return False

        # Remove spent transaction inputs from unspent_tx_outputs and add new outputs
        for tx_input in transaction["transaction_inputs"]:
            del unspent_tx_outputs[tx_input["previousOutputID"]]
        tx_id = transaction["transaction_id"]
        unspent_tx_outputs[tx_id] = {
            "id": tx_id,
            "transaction_id": tx_id,
            "recipient": transaction["receiver_address"],
            "amount": transaction["amount"],
        }
        change = inputs_sum - transaction["amount"]
        if change > 0:
            unspent_tx_outputs[tx_id + "_change"] = {
                "id": tx_id + "_change",
                "transaction_id": tx_id,
                "recipient": transaction["sender_address"],
                "amount": change,
            }

        return True
