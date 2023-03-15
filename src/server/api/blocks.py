from components.block import Block
from core.blueprint import Blueprint
from flask import current_app, request
from loguru import logger

blueprint = Blueprint("blocks", __name__)


@blueprint.route("/broadcast", methods=["POST"])
def broadcast():
    block = Block.from_json(request.json)

    logger.info("Received block {}", block.index)

    result = current_app.node.validate_block(block)
    if not result:
        current_app.node.resolve_conflict()
        return blueprint.success({"success": True, "message": "Synced blockchain."})

    current_app.node.persist_block(block)

    return blueprint.success()
