from components.transaction import Transaction
from core.blueprint import Blueprint
from flask import current_app, request
from loguru import logger

blueprint = Blueprint("transactions", __name__)


@blueprint.route("/", methods=["GET"])
def transactions():
    transactions = current_app.node.view_transactions()

    return blueprint.success({"transactions": [t.json() for t in transactions]})


@blueprint.route("/create", methods=["POST"])
def create():
    payload = request.json
    recipient_address = payload["recipient_address"]
    amount = payload["amount"]

    result = current_app.node.create_transaction(recipient_address, amount)
    if not result:
        blueprint.error(result.error)

    return blueprint.success()


@blueprint.route("/broadcast", methods=["POST"])
def broadcast():
    payload = request.json
    transaction = Transaction.from_json(payload)

    logger.info("Received transaction {}", transaction.id)

    result = current_app.node.validate_transaction(transaction)
    if not result:
        blueprint.error(result)

    current_app.node.persist_transaction(transaction)

    return blueprint.success()
