from pprint import pprint

import click
import requests


@click.group()
def cli():
    pass


@cli.command()
def balance():
    response = requests.get(f"http://0.0.0.0:5000/wallet/balance")
    if response.status_code != 200:
        raise ValueError(response.status_code)

    pprint(response.json())


@cli.command()
def transactions():
    response = requests.get(f"http://0.0.0.0:5000/transactions")
    if response.status_code != 200:
        raise ValueError(response.status_code)

    pprint(response.json())


if __name__ == "__main__":
    cli()
