import json
import typing as tp
from datetime import datetime

from pydantic import BaseModel


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


class DateTimeDecoder(json.JSONDecoder):
    def __init__(self, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, **kwargs)

    def object_hook(self, obj):
        ret = {}
        for key, value in obj.items():
            if key in {"timestamp", "whatever"}:
                ret[key] = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
            else:
                ret[key] = value
        return ret


class Serializable(BaseModel):
    # def json(self) -> str:
    #     return json.dumps(self.asdict(), cls=DateTimeEncoder)

    @classmethod
    def from_json(cls, representation: str) -> "Serializable":
        return cls.parse_raw(representation)
