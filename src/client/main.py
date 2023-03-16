import json
import typing as tp

import click
import requests
from rich.console import Console

console = Console()


@click.group()
@click.option(
    "-n",
    "--node",
    type=str,
    default="http://0.0.0.0:5000",
    show_default=True,
    help="Which node to contact",
)
@click.pass_context
def cli(ctx: click.Context, node):
    ctx.obj = {"node": node}


@cli.command()
@click.pass_obj
def balance(settings: tp.Dict[str, tp.Any]):
    response = requests.get(f"{settings['node']}/wallet/balance")
    if response.status_code != 200:
        console.print({"status": response.status_code, "error": response.json()})

    console.print(response.json())


@cli.group()
@click.pass_context
def transactions(ctx: click.Context):
    pass


@transactions.command()
@click.pass_obj
def view(settings: tp.Dict[str, tp.Any]):
    response = requests.get(f"{settings['node']}/transactions")
    if response.status_code != 200:
        console.print({"status": response.status_code, "error": response.json()})

    payload = response.json()
    transactions = payload["transactions"]

    for transaction in map(json.loads, transactions):
        console.print(f"Transaction: {transaction['id']}", style="bold")
        del transaction["id"]
        console.print_json(data=transaction, sort_keys=True)


@transactions.command()
@click.option(
    "-r",
    "--recipient",
    default="2d2d2d2d2d424547494e205055424c4943204b45592d2d2d2d2d0a4d494942496a414e42676b71686b6947397730424151454641414f43415138414d49494243674b4341514541734a765a4c2b57617358306e75584b4f704f4a550a6e4e7079577337744c6c316f647942695a7242784a30324a364f6549396265554e47374c686d2b6b444137597145693031306b7664686b71503679624c59736c0a627a52553033626e347773597a5752676c65562b42614170412f5435353339674c6d6d7032317130724c6b427563584a5546474a5976566341526b32503373460a6339413855545050527473306e34716e726d56515945584f513249795a437a6b7a48774c33617a39752b31734f6d6c78435850474e2f6e55442b36587369414c0a68342b4853362f662f47516b727969465049386c755a476f586943516870685456696d2b73476c51312b4f4b346b4b556a397167647a62684546635046456f4a0a4c5237434f545770316c45653964304b2f45484e62566c36423859443370514b5830717a577052366b6638544932642f51494f7857624b3053684e48656f4a4c0a51774944415141420a2d2d2d2d2d454e44205055424c4943204b45592d2d2d2d2d",
    type=str,
    help="The address (public key) of the recipient",
)
@click.option("-a", "--amount", type=int, help="The amount of Noobcash to transfer")
@click.pass_obj
def create(settings: tp.Dict[str, tp.Any], recipient: str, amount: int):
    payload = {"recipient_address": recipient, "amount": amount}

    response = requests.post(f"{settings['node']}/transactions/create", json=payload)
    if response.status_code != 200:
        console.print({"status": response.status_code, "error": response.json()})


if __name__ == "__main__":
    cli()
