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
    default="2d2d2d2d2d424547494e205055424c4943204b45592d2d2d2d2d0a4d494942496a414e42676b71686b6947397730424151454641414f43415138414d49494243674b434151454173704a4b41696e6a574e73716474575075462f740a3543366b464357324c3352504c5576544753567764504d5a684a51354378455034662b2f377455416947786f6d67735046334b4e4c616b6e774c4d47786a68540a73304c4950764b302b486e574d756b55504b376c426f616a4542704e333874664a7945504874476c356844784c716e5579534c72526e734a476d68314746616a0a72704365356d327871597435444d673574375435335073685174763871676958314c4c4754634647376e6b7564324e3742486b32424861746d424d4558655a4f0a6d767263744a76644c647579384f4841764a51666b34683759434b555a64395130694174616854315a34525570334d6745364363506244506a37734c5a4279410a5933785877634c354e586243684b4634346c754e7965396a4254576f72372b565979696a683773664937306d4d4f686a6f62675262684d3854665137523351310a49514944415141420a2d2d2d2d2d454e44205055424c4943204b45592d2d2d2d2d",
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
