import rich_click as click
import waitress
from components.node import Bootstrap, Peer
from core.blueprint import register_blueprints
from core.logging import setup_logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from loguru import logger
from werkzeug.exceptions import HTTPException

app = Flask(__name__)

CORS(app)


@click.command()
@click.option(
    "-i",
    "--ip",
    type=str,
    default="0.0.0.0",
    show_default=True,
    help="The ip to serve from",
)
@click.option(
    "-p",
    "--port",
    type=int,
    default=5000,
    show_default=True,
    help="The port to listen on",
)
@click.option(
    "-b",
    "--bootstrap",
    type=str,
    default=None,
    show_default=True,
    help="The address of the bootstrap node",
)
@click.option(
    "-d",
    "--difficulty",
    type=int,
    default=1,
    show_default=True,
    help="The difficulty of mining a new block",
)
@click.option(
    "-n",
    "--nodes",
    type=int,
    default=2,
    show_default=True,
    help="The total number of nodes",
)
def create_app(ip, port, bootstrap, difficulty, nodes):
    setup_logging()

    register_blueprints(app, "api")

    @app.before_request
    def _():
        logger.info(
            "{}: {} - {}",
            request.remote_addr,
            request.method,
            request.full_path,
        )

    @app.after_request
    def _(response):
        logger.info(
            "{}: {} - {} [{}] {}",
            request.remote_addr,
            request.method,
            request.full_path,
            response.status,
            response.data.decode("utf-8"),
        )
        return response

    @app.errorhandler(Exception)
    def _(error):
        code, message = 500, "Unexpected Error!"

        if isinstance(error, HTTPException):
            code, message = error.code, error.description

        logger.exception(f"{code}: {message}")

        return jsonify({"message": message}), code, {"ContentType": "application/json"}

    if bootstrap is not None:
        app.node = Peer(
            ip=ip,
            port=port,
            difficulty=difficulty,
            n_nodes=nodes,
            bootstrap_address=bootstrap,
        )
    else:
        app.node = Bootstrap(
            ip=ip,
            port=port,
            difficulty=difficulty,
            n_nodes=nodes,
            id=0,
        )

    logger.info(f"Serving at {ip}:{port}")

    waitress.serve(app, host=ip, port=port, threads=10)


if __name__ == "__main__":
    create_app()