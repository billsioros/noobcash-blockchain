from components.blockchain import Blockchain
from core.blueprint import Blueprint
from flask import current_app, request

blueprint = Blueprint("nodes", __name__)


@blueprint.route("/register", methods=["POST"])
def register():
    if not current_app.node.is_bootstrap:
        blueprint.bad_request(f"Node {current_app.node.id} is not the bootstrap node")

    payload = request.json

    node_id = current_app.node.enroll(
        f"http://{request.remote_addr}:{payload['port']}", payload["public_key"]
    )

    return blueprint.success({"id": node_id})


@blueprint.route("/enroll", methods=["POST"])
def enroll():
    if current_app.node.is_bootstrap:
        blueprint.bad_request(f"Node {current_app.node.id} is the bootstrap node")

    payload = request.json
    network = payload.get("network", None)
    blockchain = payload.get("blockchain", None)

    if not network or not blockchain:
        blueprint.bad_request("Either network or blockchain is empty or null")

    blockchain = Blockchain.from_json(blockchain)
    result = current_app.node.enroll_acknowledge(network, blockchain)
    if not result:
        blueprint.error(result)

    return blueprint.success()
