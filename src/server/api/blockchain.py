from components.block import Block
from core.blueprint import Blueprint
from flask import current_app, request
from loguru import logger

blueprint = Blueprint("blockchain", __name__)


@blueprint.route("/", methods=["GET"])
def broadcast():
    logger.info("Transmitting blockchain of node {}", current_app.node.id)

    return blueprint.success(current_app.node.blockchain.json())
