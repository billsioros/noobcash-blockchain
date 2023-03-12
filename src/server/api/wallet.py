from core.blueprint import Blueprint
from flask import current_app

blueprint = Blueprint("wallet", __name__, url_prefix="/wallet")


@blueprint.route("/balance", methods=["GET"])
def balance():
    balance = current_app.node.wallet.balance

    return blueprint.success({"balance": balance})
