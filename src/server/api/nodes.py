from components.block import Block
from components.blockchain import Blockchain
from core.blueprint import Blueprint
from flask import current_app, request
from loguru import logger

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
    blockchain = Blockchain.from_json(blockchain)

    if not network or not blockchain:
        blueprint.bad_request("Either network or blockchain is empty or null")

    result = current_app.node.validate_chain(blockchain)
    if not result:
        blueprint.error(result)

    current_app.node.network = network
    current_app.node.blockchain = blockchain

    logger.info("Node {} received network and blockchain", current_app.node.id)

    return blueprint.success()
