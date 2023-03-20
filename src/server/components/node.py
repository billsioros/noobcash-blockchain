import threading
import time
import typing as tp
from datetime import datetime
from pathlib import Path

from components import Serializable
from components.block import Block
from components.blockchain import Blockchain
from components.transaction import Transaction
from components.wallet import Wallet
from core import http
from core.result import Result
from loguru import logger
from pydantic import Field


class Node(Serializable):
    ip: str
    port: int
    capacity: int
    difficulty: int
    n_nodes: int
    blockchain: Blockchain = Field(default_factory=Blockchain)
    id: tp.Optional[int] = None
    wallet: tp.Optional[Wallet] = None
    wallets: tp.Dict[str, Wallet] = Field(default_factory=dict)
    network: tp.List[tp.Tuple[str, str]] = Field(default_factory=list)
    pending_transactions: tp.List[Transaction] = Field(default_factory=list)
    debug: bool = False
    transactions_filepath: tp.Optional[Path] = None
    metrics_: tp.Dict[str, tp.Dict[str, float]] = Field(default_factory=dict)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        threading.Thread(target=self.mining).start()

        if self.transactions_filepath is not None:
            threading.Thread(target=self.transmit_transactions).start()

    @property
    def metrics(self) -> tp.Dict[str, float]:
        n_blocks = len(self.blockchain.blocks)

        transactions = {"successful": 0, "failed": 0, "throughput": 0}
        try:
            transactions = self.metrics_["transactions"]
        except KeyError:
            pass

        return {
            "transactions": transactions,
            "blocks": {
                "mining_time": self.metrics_["blocks"]["mining_time"] / n_blocks,
                "total_time": self.metrics_["blocks"]["total_time"] / n_blocks,
            },
        }

    @property
    def is_bootstrap(self) -> bool:
        return self.id == 0

    def generate_wallet(self, public_key: str, private_key: str) -> None:
        if self.debug:
            self.wallet = Wallet(public_key=public_key, private_key=private_key)
        else:
            self.wallet = Wallet.generate_wallet()

        self.wallets[self.wallet.public_key] = self.wallet

        logger.info("Registered wallet address '{}'", self.wallet.public_key)

    def create_transaction(self, recipient_address: str, amount: int) -> Result:
        if recipient_address not in self.wallets:
            return Result.not_found(f"Unknown receipient '{recipient_address}'")

        if recipient_address == self.wallet.public_key:
            return Result.conflict(f"Recipient and sender addresses are identical.")

        if amount <= 0:
            return Result.invalid(f"Invalid transaction amount '{amount}'")

        logger.info("Creating transaction")

        counter, i, transaction_inputs = amount, 0, []
        while counter > 0 and i < len(self.wallet.utxos):
            id, _, _, transaction_amount = self.wallet.utxos[i]

            if counter - transaction_amount > 0:
                transaction_inputs.append(id)
                counter -= transaction_amount
            elif counter - transaction_amount == 0:
                transaction_inputs.append(id)
                counter = 0
            else:
                transaction_inputs.append(id)
                counter = 0

            i += 1

        transaction = Transaction.create_transaction(
            self.wallet.public_key,
            recipient_address,
            amount,
            transaction_inputs,
            [],
            self.wallet.private_key,
        )

        change = self.wallet.balance - amount
        transaction.transaction_outputs = [
            (f"{self.id}:{transaction.id}", transaction.id, recipient_address, amount),
            (
                f"{self.id}:{transaction.id}",
                transaction.id,
                self.wallet.public_key,
                change,
            ),
        ]

        result = self.validate_transaction(transaction)
        if not result:
            return result

        self.persist_transaction(transaction)

        self.broadcast_transaction(transaction)

        return Result.ok()

    def calculate_change(self, transaction: Transaction) -> int:
        wallet = self.wallets[transaction.sender_address]

        total = 0
        for utxo in wallet.utxos:
            if utxo[0] in transaction.transaction_inputs:
                total += utxo[3]

        return total - transaction.amount

    def validate_transaction(self, transaction: Transaction) -> Result:
        logger.info("Validating transaction {}", transaction.id)

        if not transaction.verify_signature():
            return Result.invalid(f"Invalid transaction signature {transaction.id}")

        if self.calculate_change(transaction) < 0:
            return Result.invalid(f"Invalid transaction amount {transaction.id}")

        return Result.ok()

    def persist_transaction(self, transaction: Transaction) -> None:
        logger.info("Persisting transaction {}", transaction.id)
        self.update_wallets(transaction)

        self.pending_transactions.append(transaction)

    def update_wallets(self, transaction: Transaction) -> None:
        wallet = self.wallets[transaction.recipient_address]
        wallet.utxos.append(transaction.transaction_outputs[0])

        wallet = self.wallets[transaction.sender_address]

        i = 0
        while i < len(wallet.utxos):
            if wallet.utxos[i][0] in transaction.transaction_inputs:
                del wallet.utxos[i]

            i += 1

        wallet.utxos.append(transaction.transaction_outputs[1])

    def broadcast_transaction(self, transaction: Transaction) -> None:
        logger.info("Broadcasting transaction {}", transaction.id)

        for remote_address, _ in self.network[: self.id] + self.network[self.id + 1 :]:
            logger.info(
                "Transmitting transaction {} to {}", transaction.id, remote_address
            )

            http.post(f"{remote_address}/transactions/broadcast", transaction)

    def view_transactions(self) -> tp.List[Transaction]:
        if self.debug:
            return self.blockchain.blocks[-1].transactions + self.pending_transactions

        return self.blockchain.blocks[-1].transactions

    def mining(self):
        self.metrics_["blocks"] = {"mining_time": 0, "total_time": 0}

        while True:
            if len(self.pending_transactions) < self.capacity:
                time.sleep(5)
                continue

            now = time.time()

            block = Block(
                index=len(self.blockchain.blocks),
                timestamp=datetime.utcnow(),
                nonce=0,
                previous_hash=self.blockchain.blocks[-1].current_hash,
                transactions=self.pending_transactions,
            )

            logger.info("Mining block {}", block.index)
            self.mine_block(block)
            logger.info("Finished mining block {}", block.index)

            self.metrics_["blocks"]["mining_time"] += time.time() - now

            result = self.validate_block(block)
            if not result:
                logger.error(result.error.message)
                continue

            self.persist_block(block)
            self.broadcast_block(block)

            self.metrics_["blocks"]["total_time"] += time.time() - now

    def mine_block(self, block: Block):
        """
        Mine a new block by finding a nonce that makes the block hash start with a certain
        number of zeroes determined by the difficulty constant.
        """
        # Keep trying different values of the nonce until the block hash starts with
        # the required number of zeroes
        target, current_hash = "0" * self.difficulty, Block.calculate_hash(block)
        while not current_hash.startswith(target):
            block.nonce += 1
            current_hash = Block.calculate_hash(block)

        block.current_hash = current_hash

    def validate_block(self, block: Block, previous_block: tp.Optional[Block] = None):
        if previous_block is None:
            previous_block = self.blockchain.blocks[-1]

        # Check if block's current hash is correct
        block_hash = Block.calculate_hash(block)
        if block_hash != block.current_hash:
            return Result.invalid(f"Block {block.index} has incorrect hash")

        # Check if block's previous hash is equal to hash of previous block
        if block.previous_hash != previous_block.current_hash:
            return Result.invalid(f"Block {block.index} previous hash mismatch")

        return Result.ok()

    def persist_block(self, block: Block):
        self.pending_transactions.clear()
        self.blockchain.blocks.append(block)

    def broadcast_block(self, block: Block):
        logger.info("Broadcasting block {}", block.index)

        for remote_address, _ in self.network[: self.id] + self.network[self.id + 1 :]:
            logger.info("Transmitting block {} to {}", block.index, remote_address)

            http.post(f"{remote_address}/blocks/broadcast", block)

    def validate_chain(self, blockchain: Blockchain) -> Result:
        for i in range(1, len(blockchain.blocks)):
            previous_block = blockchain.blocks[i - 1]
            current_block = blockchain.blocks[i]

            result = self.validate_block(current_block, previous_block)
            if not result:
                return result

        return Result.ok()

    def resolve_conflict(self) -> None:
        logger.info("Resolving conflict")

        longest_block_chain = self.blockchain

        # Find the longest chain from all the neighboring nodes
        max_length = len(longest_block_chain.blocks)
        for remote_address, _ in self.network[: self.id] + self.network[self.id + 1 :]:
            logger.info("Retrieving blockchain from {}", remote_address)

            response = http.get(f"{remote_address}/blockchain/")

            payload = response.json()
            blockchain = Blockchain.from_json(payload)
            length = len(blockchain.blocks)

            # Check if the length is longer and the chain is valid
            if self.validate_chain(blockchain) and length > max_length:
                max_length, longest_block_chain = length, blockchain

        # Replace the current blockchain with the new blockchain if it is longer and valid
        self.blockchain = longest_block_chain

    def transmit_transactions(self):
        while len(self.network) < self.n_nodes:
            time.sleep(1)

        self.metrics_["transactions"] = {"successful": 0, "failed": 0, "throughput": 0}

        logger.info("Reading transaction file {}", self.transactions_filepath)

        now = time.time()
        with self.transactions_filepath.open("r") as file:
            for node_id, amount in map(str.split, file.readlines()):
                node_id, amount = int(node_id[2:]), int(amount)
                _, receiver_address = self.network[node_id]

                result = self.create_transaction(receiver_address, amount)
                if result:
                    self.metrics_["transactions"]["successful"] += 1
                else:
                    self.metrics_["transactions"]["failed"] += 1

        elapsed = time.time() - now

        n_successful_transactions = self.metrics_["transactions"]["successful"]
        n_failed_transactions = self.metrics_["transactions"]["failed"]
        n_transactions = n_successful_transactions + n_failed_transactions

        self.metrics_["transactions"]["throughput"] = n_transactions / elapsed

        logger.info("Finished reading file {}", self.transactions_filepath)


class EnrollRequest(Serializable):
    network: tp.List[tp.Tuple[str, str]]
    blockchain: Blockchain
    wallets: tp.List[Wallet]


class Bootstrap(Node):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        public_key = b"2d2d2d2d2d424547494e205055424c4943204b45592d2d2d2d2d0a4d494942496a414e42676b71686b6947397730424151454641414f43415138414d49494243674b434151454173704a4b41696e6a574e73716474575075462f740a3543366b464357324c3352504c5576544753567764504d5a684a51354378455034662b2f377455416947786f6d67735046334b4e4c616b6e774c4d47786a68540a73304c4950764b302b486e574d756b55504b376c426f616a4542704e333874664a7945504874476c356844784c716e5579534c72526e734a476d68314746616a0a72704365356d327871597435444d673574375435335073685174763871676958314c4c4754634647376e6b7564324e3742486b32424861746d424d4558655a4f0a6d767263744a76644c647579384f4841764a51666b34683759434b555a64395130694174616854315a34525570334d6745364363506244506a37734c5a4279410a5933785877634c354e586243684b4634346c754e7965396a4254576f72372b565979696a683773664937306d4d4f686a6f62675262684d3854665137523351310a49514944415141420a2d2d2d2d2d454e44205055424c4943204b45592d2d2d2d2d"
        private_key = b"2d2d2d2d2d424547494e205253412050524956415445204b45592d2d2d2d2d0a4d4949457041494241414b434151454173704a4b41696e6a574e73716474575075462f743543366b464357324c3352504c5576544753567764504d5a684a51350a4378455034662b2f377455416947786f6d67735046334b4e4c616b6e774c4d47786a685473304c4950764b302b486e574d756b55504b376c426f616a4542704e0a333874664a7945504874476c356844784c716e5579534c72526e734a476d68314746616a72704365356d327871597435444d67357437543533507368517476380a71676958314c4c4754634647376e6b7564324e3742486b32424861746d424d4558655a4f6d767263744a76644c647579384f4841764a51666b34683759434b550a5a64395130694174616854315a34525570334d6745364363506244506a37734c5a4279415933785877634c354e586243684b4634346c754e7965396a4254576f0a72372b565979696a683773664937306d4d4f686a6f62675262684d3854665137523351314951494441514142416f49424141776d4e356153324d4c5867336d370a4554694e503074596349576c354c4778467a393430704f614346384f6d4b4238634b3662386a475251394c5a4a31794179724f6256384d6a77693732664b76480a796d6a5456582b445a6b6f6847336178334754526c70544433665675464e7451504e626965485a364d58514b64622f7a7a474c39503072526630496e396841330a7865713658302f4e79312f59572f3978363749577a395637774d6d373537554974444c685049452b792f6445544e333877566238564e376770767a6f4638494c0a41747578486262775035583763664137686171666946694351597a48374531686b6a3338682f4976374f5872636938526e366339575149427478706157766d6c0a387171304e77785946716b6771775234494377384a4b7a45686e54782f785a6a6e6c61415245424e4144302b63586f774a5a78456646697772424f44644355360a757130426e6d6b43675945417a75333830332f566b344e6f654b59504258784758303843475169573572566a51316330437a6c5a302f452f4e5264584f2f51300a73687835593742792f4942305a466f45357757512b6a3544377131364874707074316b6e5844614d61356d69434c61695063524f773441626b655a534a6f482b0a58366d44473054306b2b3071786542585269476d306f6d48466b2b3131536c686468646e5a4f577276366334476a757869644353734d6b4367594541334f72450a38395a51694c6930474f635755417155326c4e41563646624742774a70776841767a35743752656a6e495577514b55324f46564956657a3734534176527856480a7870375a6634305a6e316e6c39776f4d4270344d384c3979704c5a3961494b58352b363243486844337a34383449424b7a4832576a55587a4b73664c454659710a2f312b5879416a324657736a455261425659557653667130385451695244355265342b66705a6b436759416266347136664746675966555047316f68713373610a6a554246485677594f6f422f5957593847356e7854547a4f4446542b565a787645744f61794d6276415137326976506430324b4a7270364f6143557a566d6a340a415850326b42556d383171523939736c684348485877334b334b574d456e68414e43474644537648514a7750675a6c336131396b325076486e6a34576e7049690a424567734930306f6763733179547231696d384436514b42675143756b556d65304f79456a55657249666773755a2f5551644c6e4c4262366e7a5531617a30570a6f6a4e6c4662667775414a674975304d614c2b6e506f5075366d725268637859394338304c6f4266766a384e446b4267666b594665354d512b79397742546f610a535452497a786636385968546371306f6c396a2b753561696149786131577857726567585a70566d61576d6c5742354e514e6755596d725736765a6b374d57670a6d4f5a7a69514b426751436a5832564a3635367a777771624c2f57316f316e4e585148354349617348575a67696c6d50555a684a565a67734f6135324c4d78420a6f6f6375634d6479502f76463277484d687049336a586e5251546d373077685844424b565673575344393777526f5a6146624a78676f4d4c4871486b497351300a50366b2f5448684d656747682f4f2f646433727539726f3967694f355a6b4b386e2f624c6d2b64694671504344674276766a4d4579773d3d0a2d2d2d2d2d454e44205253412050524956415445204b45592d2d2d2d2d"

        self.generate_wallet(public_key, private_key)

        self.network.append((f"http://{self.ip}:{self.port}", self.wallet.public_key))

        transaction = Transaction.create_transaction(
            "0",
            self.wallet.public_key,
            100 * self.n_nodes,
            [],
            [],
            self.wallet.private_key,
        )

        transaction.transaction_outputs = [
            (
                f"{self.id}:{transaction.id}",
                transaction.id,
                self.wallet.public_key,
                100 * self.n_nodes,
            ),
            (f"{self.id}:{transaction.id}", transaction.id, "0", 0),
        ]

        self.wallet.utxos = [
            transaction.transaction_outputs[0],
        ]

        genesis_block = Block(
            index=0,
            timestamp=datetime.utcnow(),
            nonce=0,
            previous_hash=1,
            transactions=[transaction],
        )

        genesis_block.current_hash = Block.calculate_hash(genesis_block)

        self.blockchain.blocks.append(genesis_block)

    def enroll(self, remote_address: str, public_key: str) -> int:
        logger.info("Registering {}", remote_address)

        self.network.append((remote_address, public_key))
        self.wallets[public_key] = Wallet(public_key=public_key, utxos=[])

        if len(self.network) == self.n_nodes:
            for remote_address, public_key in self.network[1:]:
                logger.info("Enrolling {}", remote_address)

                http.post(
                    f"{remote_address}/nodes/enroll",
                    EnrollRequest(
                        network=self.network,
                        blockchain=self.blockchain,
                        wallets=list(self.wallets.values()),
                    ),
                )

            time.sleep(5)

            for remote_address, public_key in self.network[1:]:
                self.create_transaction(public_key, 100)

        return len(self.network) - 1

    def gather_metrics(self) -> tp.Dict[str, tp.Dict[str, float]]:
        global_metrics = {
            "transactions": {
                "total_successful": 0,
                "total_failed": 0,
                "average_throughput": 0,
            },
            "blocks": {"average_mining_time": 0, "average_total_time": 0},
        }

        for remote_address, _ in self.network[: self.id] + self.network[self.id + 1 :]:
            logger.info("Gathering metrics for {}", remote_address)

            response = http.get(f"{remote_address}/metrics/")
            local_metrics = response.json()

            global_metrics["transactions"]["total_successful"] += local_metrics[
                "transactions"
            ]["successful"]
            global_metrics["transactions"]["total_failed"] += local_metrics[
                "transactions"
            ]["failed"]
            global_metrics["transactions"]["average_throughput"] += (
                local_metrics["transactions"]["throughput"] / self.n_nodes
            )

            global_metrics["blocks"]["average_mining_time"] += (
                local_metrics["blocks"]["mining_time"] / self.n_nodes
            )
            global_metrics["blocks"]["average_total_time"] += (
                local_metrics["blocks"]["total_time"] / self.n_nodes
            )

        return global_metrics


class Peer(Node):
    bootstrap_address: tp.Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        public_key = b"2d2d2d2d2d424547494e205055424c4943204b45592d2d2d2d2d0a4d494942496a414e42676b71686b6947397730424151454641414f43415138414d49494243674b4341514541734a765a4c2b57617358306e75584b4f704f4a550a6e4e7079577337744c6c316f647942695a7242784a30324a364f6549396265554e47374c686d2b6b444137597145693031306b7664686b71503679624c59736c0a627a52553033626e347773597a5752676c65562b42614170412f5435353339674c6d6d7032317130724c6b427563584a5546474a5976566341526b32503373460a6339413855545050527473306e34716e726d56515945584f513249795a437a6b7a48774c33617a39752b31734f6d6c78435850474e2f6e55442b36587369414c0a68342b4853362f662f47516b727969465049386c755a476f586943516870685456696d2b73476c51312b4f4b346b4b556a397167647a62684546635046456f4a0a4c5237434f545770316c45653964304b2f45484e62566c36423859443370514b5830717a577052366b6638544932642f51494f7857624b3053684e48656f4a4c0a51774944415141420a2d2d2d2d2d454e44205055424c4943204b45592d2d2d2d2d"
        private_key = b"2d2d2d2d2d424547494e205253412050524956415445204b45592d2d2d2d2d0a4d4949456f67494241414b4341514541734a765a4c2b57617358306e75584b4f704f4a556e4e7079577337744c6c316f647942695a7242784a30324a364f65490a396265554e47374c686d2b6b444137597145693031306b7664686b71503679624c59736c627a52553033626e347773597a5752676c65562b42614170412f54350a353339674c6d6d7032317130724c6b427563584a5546474a5976566341526b32503373466339413855545050527473306e34716e726d56515945584f513249790a5a437a6b7a48774c33617a39752b31734f6d6c78435850474e2f6e55442b36587369414c68342b4853362f662f47516b727969465049386c755a476f586943510a6870685456696d2b73476c51312b4f4b346b4b556a397167647a62684546635046456f4a4c5237434f545770316c45653964304b2f45484e62566c36423859440a3370514b5830717a577052366b6638544932642f51494f7857624b3053684e48656f4a4c5177494441514142416f494241454831347a635658534a664b5341460a4869754d384b636f6d7a38354f374a755a7037666449442f387a4d4872624e55446e3466553359467a33506c62484b6f644e6a645674563157776d54756f6a500a6b61462f3737704a35456961683137762f524a78492f573449636f2b47444f48496e4d4979735a71356d7172785145686b2f68725735586f3768514d715a45720a646d78644b5273704d653375474d4e52436156777074486d7577394a51397a30564b2b7047726c644870555138686e6874616844485273502b2b70556a52506c0a6c6e306a686d64736a2b34476a4933585352432b695a72676968432f386e6852342b68472b724e6e78506c464c705049793474714a5839614a57464f646141480a54415a384438573257796c5839784774487a2f5574385078667950686a6a5674304e6478303063546d306a4b46775a3757344c32746f6630396d306c316d786f0a6f3370666c30454367594541786f6f45436b574131675a475033666650797a4b715254384732586967574c4f356e38305270662b646b6c6f646a46356c3247780a7663366f5854496b314968744455636c79557131374143694b79684e6468464241787248674d645444776565356c356f7a7647746a6f577a303655654e4a49390a582f7a4d4773364f49697632473876526d31706e7538747170364b586c375465395a456a524967395866796a656e7a7771793256454f4d436759454134376a390a50383866366f2b64367052764679723554765776594d506e74676b52332f6d456d316f59324233725038346a354264574239357877753566726d4234437a63370a45356f78533270684b4477452b4f736b6850514230614c3865416d484a747542565143326e356a4931525645565276664734332f386d59366d4e67506a35474a0a3731505741366d4d4358535a4478506334442b41387137642b575652744e594752324b6f79694543675942637871666d714e3377705a5030477138504658354b0a6a737a55664d4c673157783731357431465a664b624c6c4d366765347a75564248693464427336684a6e4e58546855425146464d7a4772376f655334744931640a78776a4e5339657259564e477358316d6e78634d543778647658346b384f5750556c474b67565633384855635068316637466f6e4c6f4a54666134374c5545330a4862434f574e2f63614b3934454b52695358577349774b426745416141712f446a69686f3550727a625a49483973585451747271536e396a626a53742b4459430a3170742f55496c56626154334c4c427158587552766a3148796f4c6475544e375a41546d6e524c47556c2f2f555068623932636269685941474a74486a7442750a73766d5a2b47364333676c5848796153676b6d706e54554a484e673944366265346f2b46576e594f37456269514871665a5a7a717648464870416854647445420a5a4b4942416f47416463586f484a61496e4d612f49677a78665865397532734b447a5a5948612f412b616a374465306843626349396f37686255674b656334670a6c786454436359566a76546755354152547073356d51334f316178705a424d365561433357577355446939386d4944733647726f354a334741524532486c33390a4250316153346b4a697964746c563834744b305039542b4e456166774f345a6b614e3152475475734233717a684838777072733d0a2d2d2d2d2d454e44205253412050524956415445204b45592d2d2d2d2d"

        self.generate_wallet(public_key, private_key)

        threading.Thread(target=self.register).start()

    def register(self) -> None:
        assert self.id is None, f"Node has already been assigned id {self.id}"

        # Send my public key to the bootstrap node
        response = http.post(
            f"{self.bootstrap_address}/nodes/register",
            {"port": self.port, "public_key": self.wallet.public_key},
        )
        payload = response.json()

        self.id = payload["id"]

        logger.info("Received id: {}", self.id)

    def enroll_acknowledge(
        self,
        network: tp.List[tp.Tuple[str, str]],
        blockchain: Blockchain,
        wallets: tp.List[Wallet],
    ) -> Result:
        result = self.validate_chain(blockchain)
        if not result:
            return result

        self.network = network
        self.blockchain = blockchain
        for wallet in wallets:
            if wallet.public_key != self.wallet.public_key:
                self.wallets[wallet.public_key] = wallet

        logger.info("Node {} received network and blockchain", self.id)

        return Result.ok()
