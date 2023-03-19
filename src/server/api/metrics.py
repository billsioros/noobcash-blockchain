from core.blueprint import Blueprint
from flask import current_app

blueprint = Blueprint("metrics", __name__)


@blueprint.route("/", methods=["GET"])
def view():
    return blueprint.success(current_app.node.metrics)


@blueprint.route("/total", methods=["GET"])
def total():
    if not current_app.node.is_bootstrap:
        blueprint.bad_request(f"Node {current_app.node.id} is not the bootstrap node")

    return blueprint.success(current_app.node.gather_metrics())
