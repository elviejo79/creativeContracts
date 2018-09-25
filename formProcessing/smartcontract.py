import solc
from web3 import Web3, HTTPProvider, IPCProvider
from eth_account import Account
from web3.middleware import geth_poa_middleware


class SmartContract:
    def __init__(self, node_uri, use_ipc=False, use_poa=False):
        if use_ipc:
            provider = IPCProvider(node_uri)
        else:
            provider = HTTPProvider(node_uri)

        self.w3 = Web3(provider)
        self.default_account = None
        self.contract_data = None

        if use_poa:
            # Needed only with PoA (Rinkeby)
            self.w3.middleware_stack.inject(geth_poa_middleware, layer=0)

    def validate_to_checksum(self, address):
        if not Web3.isAddress(address):
            raise ValueError('Not a valid account address: ' + address)

        if not Web3.isChecksumAddress(address):
            return Web3.toChecksumAddress(address)

        return address

    def validate_contract_data(self, contract_data):
        missing_attributes = []

        # Validate expected attributes are pressent
        if 'customer_address' not in contract_data:
            missing_attributes.append('customer_address')

        if 'oracle_address' not in contract_data:
            missing_attributes.append('oracle_address')

        if 'contract_amount' not in contract_data:
            missing_attributes.append('contract_amount')

        if 'oracle_fee' not in contract_data:
            missing_attributes.append('oracle_fee')

        if 'lcurl' not in contract_data:
            missing_attributes.append('lcurl')

        if 'lchash' not in contract_data:
            missing_attributes.append('lchash')

        if 'contract_duedate_ts' not in contract_data:
            missing_attributes.append('contract_duedate_ts')

        if 'contract_settlement_ts' not in contract_data:
            missing_attributes.append('contract_settlement_ts')

        if 'contract_delivery_ts' not in contract_data:
            missing_attributes.append('contract_delivery_ts')

        if missing_attributes:
            raise AttributeError('Missing attributes: ' +
                                 ', '.join(missing_attributes))
        return True

    def set_contract_data(self, **kwargs):
        self.validate_contract_data(
            kwargs)  # Raise exception with missing values

        # Sample values for expected attributes:
        # customer_address = Web3.toChecksumAddress("0x14723a09acff6d2a60dcdf7aa4aff308fddc160c")
        # oracle_address = Web3.toChecksumAddress("0x4b0897b0513fdc7c541b6d9d7e929c4e5364d2db")
        # contract_amount = 10
        # oracle_fee = 1
        # lcurl = "http://www.creativecontract.org"
        # lchash = "B221D9DBB083A7F33428D7C2A3C3198AE925614D70210E28716CCAA7CD4DDB79"
        # contract_duedate_ts = 1544779800000
        # contract_settlement_ts = 1545384600000
        # contract_delivery_ts = 1546384600000

        # Valid ethereum addresses should be given
        kwargs['customer_address'] = self.validate_to_checksum(
            kwargs['customer_address'])
        kwargs['oracle_address'] = self.validate_to_checksum(
            kwargs['oracle_address'])

        self.contract_data = kwargs

    def set_deployment_account(self, public_key):
        self.default_account = self.validate_to_checksum(public_key)

    def import_account(self, private_key, passphrase, as_default=True):
        # Check if address exists
        public_key = Account.privateKeyToAccount(private_key).address

        if public_key not in self.w3.eth.accounts:
            # Add a sample wallet with funds
            self.w3.personal.importRawKey(private_key, passphrase)

        # Unlock wallet to allow outgoing transactions
        default_account = public_key
        # TODO Use the flask app's logger instead of print to stdout directly
        print('Will use account: ', default_account)

        is_unlocked = self.w3.personal.unlockAccount(default_account,
                                                     passphrase)
        if not is_unlocked:
            # TODO Use the flask app's logger instead of print to stdout directly
            print("Can't use the account, deploy won't happen:",
                  default_account)
            return None

        if as_default:
            self.default_account = self.validate_to_checksum(public_key)

        return public_key

    def deploy_compiled(self, abi, bytecode):
        if not (self.default_account and self.contract_data):
            raise ValueError(
                'Set up account and contract data before deploying')

        # Instantiate and deploy contract
        contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)

        # TODO Can use this to estimate gas and log that out
        # https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.estimateGas

        tx_hash = contract.constructor(**self.contract_data).transact({
            'from':
            self.default_account
        })

        # TODO Make async with: waitForTransactionReceipt
        #      Default timeout: 120
        # TODO Adjust the timeout using info from https://ethgasstation.info/

        # Get tx receipt to get contract address
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)

        return tx_receipt['contractAddress']  # Return contract address

    def deploy(self, contract_name, contract_source_code):
        if not (self.default_account and self.contract_data):
            raise ValueError(
                'Set up account and contract data before deploying')

        compiled_sol = solc.compile_source(contract_source_code, optimize=True)
        contract_interface = compiled_sol['<stdin>:' + contract_name]

        return self.deploy_compiled(contract_interface['abi'],
                                    contract_interface['bin'])
