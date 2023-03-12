from components.block import Block
from components.blockchain import Blockchain
from core.blueprint import Blueprint
from flask import current_app, request
from loguru import logger

blueprint = Blueprint("nodes", __name__, url_prefix="/nodes")


@blueprint.route("/register", methods=["POST"])
def register():
    if not current_app.node.is_bootstrap:
        blueprint.bad_request(f"Node {current_app.node.id} is not the bootstrap node")

    payload = request.get_json()

    node_id = current_app.node.enroll(
        f"http://{request.remote_addr}:{payload['port']}", payload["public_key"]
    )

    return blueprint.success({"id": node_id})


@blueprint.route("/enroll", methods=["POST"])
def enroll():
    if current_app.node.is_bootstrap:
        blueprint.bad_request(f"Node {current_app.node.id} is the bootstrap node")

    payload = request.get_json()

    network = payload.get("network", None)

    block_chain = payload.get("block_chain", None)
    block_chain = Blockchain.from_json(block_chain)

    if not network or not block_chain:
        blueprint.bad_request("Either network or blockchain is empty or null")

    for i in range(len(block_chain) - 1):
        if not block_chain[i].validate_block(block_chain[i] - 1):
            blueprint.bad_request("Invalid block chain")

    current_app.node.network = network
    current_app.node.block_chain = block_chain

    logger.info("Node {} received network and block_chain", current_app.node.id)

    return blueprint.success()
