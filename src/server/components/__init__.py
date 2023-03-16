import typing as tp

from pydantic import BaseModel


class Serializable(BaseModel):
    @classmethod
    def from_json(
        cls, representation: tp.Union[str, tp.Dict[str, tp.Any]]
    ) -> "Serializable":
        if isinstance(representation, dict):
            return cls.parse_obj(representation)
        elif isinstance(representation, str):
            return cls.parse_raw(representation)
        else:
            raise TypeError(f"Parsing '{type(representation)}' is not supported")
