from components.transaction import Transaction
from core.blueprint import Blueprint
from flask import current_app, request
from loguru import logger

blueprint = Blueprint("transactions", __name__, url_prefix="/transactions")


@blueprint.route("/", methods=["GET"])
def transactions():
    transactions = current_app.node.block_chain.blocks[-1].transactions

    return blueprint.success({"transactions": [t.json() for t in transactions]})


@blueprint.route("/broadcast", methods=["POST"])
def broadcast():
    payload = request.json
    transaction = Transaction.from_json(payload)

    logger.info("Received transaction {}", transaction.id)

    current_app.node.block_chain.add_transaction(transaction)

    # current_app.node.validate_transaction(payload)

    return blueprint.success()
