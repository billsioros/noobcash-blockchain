from components.blockchain import Blockchain
from components.wallet import Wallet
from core.blueprint import Blueprint
from flask import current_app, request

blueprint = Blueprint("nodes", __name__)


@blueprint.route("/register", methods=["POST"])
def register():
    if not current_app.node.is_bootstrap:
        blueprint.bad_request(f"Node {current_app.node.id} is not the bootstrap node")

    payload = request.json

    remote_address = request.remote_addr
    if current_app.config["USE_IPV6"]:
        remote_address = f"[{remote_address}]"

    node_id = current_app.node.enroll(
        f"http://{remote_address}:{payload['port']}", payload["public_key"]
    )

    return blueprint.success({"id": node_id})


@blueprint.route("/enroll", methods=["POST"])
def enroll():
    if current_app.node.is_bootstrap:
        blueprint.bad_request(f"Node {current_app.node.id} is the bootstrap node")

    payload = request.json
    network = payload.get("network", None)
    blockchain = payload.get("blockchain", None)
    wallets = payload.get("wallets", None)

    if not network or not blockchain:
        blueprint.bad_request("Either network or blockchain is empty or null")

    blockchain = Blockchain.from_json(blockchain)
    wallets = [Wallet.from_json(wallet) for wallet in wallets]
    result = current_app.node.enroll_acknowledge(network, blockchain, wallets)
    if not result:
        blueprint.error(result.error)

    return blueprint.success()
