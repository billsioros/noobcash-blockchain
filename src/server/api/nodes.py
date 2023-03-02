import json

from core.blueprint import Blueprint
from flask import current_app, request
from loguru import logger

blueprint = Blueprint("nodes", __name__, url_prefix="/nodes")


@blueprint.route("/register", methods=["POST"])
def register():
    if not current_app.node.is_bootstrap:
        blueprint.bad_request(f"Node {current_app.node.id} is not the bootstrap node")

    payload = request.get_json()

    node_id = current_app.node.add_to_ring(
        f"http://{request.remote_addr}:{payload['port']}"
    )

    return blueprint.success({"id": node_id})


@blueprint.route("/routing-table", methods=["POST"])
def routing_table():
    if current_app.node.is_bootstrap:
        blueprint.bad_request(f"Node {current_app.node.id} is the bootstrap node")

    current_app.node.routing_table = request.get_json()

    logger.info("Retrieved ring")

    return blueprint.success()
