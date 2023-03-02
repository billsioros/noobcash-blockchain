from core.blueprint import Blueprint

blueprint = Blueprint("transactions", __name__, url_prefix="/transactions")


@blueprint.route("/get", methods=["GET"])
def get_transactions():
    transactions = blockchain.transactions

    response = {"transactions": transactions}
    return blueprint.success(response)
