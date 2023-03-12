import typing as tp

import requests
from loguru import logger


def get(url: str):
    logger.info("GET {}", url)

    return requests.get(url)


def post(url: str, payload: tp.Any) -> tp.Optional[tp.Dict[str, tp.Any]]:
    logger.info("POST {}", url)

    if not isinstance(payload, dict):
        payload = payload.json()

    response = requests.post(url, json=payload)
    if response.status_code != 200:
        logger.error("POST {} failed [{}]", url, response.status_code)

    try:
        return response
    except Exception as e:
        logger.error("POST {} failed [{}]", e)
