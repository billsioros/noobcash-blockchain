import json
import typing as tp
from http import HTTPStatus

from core.error import Error
from flask import Flask, abort
from flask.blueprints import Blueprint as BaseBlueprint
from werkzeug.utils import find_modules, import_string


def register_blueprints(app: Flask, path: str) -> None:
    for name in find_modules(path, recursive=True):
        mod = import_string(name)
        if hasattr(mod, "blueprint"):
            app.register_blueprint(mod.blueprint)


class Blueprint(BaseBlueprint):
    def __init__(self, *args: tp.Tuple[tp.Any], **kwargs: tp.Dict[str, tp.Any]):
        super().__init__(*args, **{**kwargs, "url_prefix": f"/{args[0]}"})

    def error(self, *args: tp.Tuple[tp.Any]) -> None:
        if len(args) == 1 and isinstance(args[0], Error):
            abort(args[0].error_type, args[0].message)
        else:
            status, message = args[0]
            abort(status, {"message": message})

    def bad_request(self, message: str):
        self.error(HTTPStatus.BAD_REQUEST, message)

    def success(self, payload: tp.Optional[tp.Any] = None):
        if payload is None:
            payload = {"success": True}

        return json.dumps(payload), 200, {"ContentType": "application/json"}
