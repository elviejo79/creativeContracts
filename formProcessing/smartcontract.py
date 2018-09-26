import solc
from web3 import Web3, HTTPProvider, IPCProvider, middleware
from web3.gas_strategies.time_based import construct_time_based_gas_price_strategy
from eth_account import Account


class SmartContract:
    """ Simple client to handle contract deployment.

    Attributes:
        w3 (object): Instance of the web3 client.
        default_account (str): Ethereum address to use for contract deployment.
        contract_data (dict): Dict containing contract's constructor arguments.
    """

    def __init__(self, node_uri, use_ipc=False, use_poa=False):
        """ Create instance to interact with the contract deployer.

        Args:
            node_uri (str): Either the http address of an ethereum node or the
                      path to the IPC file if 'use_ipc=True'.
            use_ipc (bool): If True then 'node_uri' will be treated as a file
                     path to the 'geth.ipc' file of the node to connect to.
            use_poa (bool): If True then it will inject 'geth_poa_middleware'
                     to the web3 instance. When 'node_uri' refers to a Rinkeby
                     node then this needs to be set to True.
        """
        if use_ipc:
            provider = IPCProvider(node_uri)
        else:
            provider = HTTPProvider(node_uri)

        self.w3 = Web3(provider)
        self.default_account = None
        self.contract_data = None

        if use_poa:
            # Needed only with PoA (Rinkeby)
            self.w3.middleware_stack.inject(
                middleware.geth_poa_middleware, layer=0)

        block_sample = 40
        prob = 95  # Probability to be included
        express_strategy = construct_time_based_gas_price_strategy(
            30, block_sample, prob)

        self.w3.eth.setGasPriceStrategy(express_strategy)
        # Tries to make transactions faster (and more expensive?)
        # self.w3.eth.setGasPriceStrategy(fast_gas_price_strategy)
        self.w3.middleware_stack.add(middleware.time_based_cache_middleware)
        self.w3.middleware_stack.add(
            middleware.latest_block_based_cache_middleware)
        self.w3.middleware_stack.add(middleware.simple_cache_middleware)

    def validate_to_checksum(self, address):
        """ Validate given Ethereum address and change to checksum version.

        Args:
             address (str): Ethereum address to validate.

        Returns:
             str: The checksum address ensured to be valid.

        Raises:
            ValueError: If the given address is not a valid Ethereum address.
        """
        if not Web3.isAddress(address):
            raise ValueError('Not a valid account address: ' + address)

        if not Web3.isChecksumAddress(address):
            return Web3.toChecksumAddress(address)

        return address

    def validate_contract_data(self, contract_data):
        """ Validate contract's constructor data.

        Args:
            contract_data (dict): Dict containing contract's constructor
                arguments.

        Returns:
            bool: True if data is valid.

        Raises:
            AttributeError: If 'contract_data' is missing a field needed for
                the contract deployment.
        """
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
        """ Fill contract's constructor arguments to deploy.

        Args:
            customer_address (str): Customer's Ethereum address.
            oracle_address (str): Oracle's Ethereum address.
            contract_amount (int): Amount to be paid to the contract.
            oracle_fee (int): Fee to be paid to the Oracle for its validation
                services.
            lcurl (str): Legal contract URL where a textual representation of
                the contract exists.
            lchash (str): Hash SHA256 of the legal contract document to ensure
                textual representation of the contract hasn't been tampered.
            contract_duedate_ts (int): Contract's due date in UNIX timestamp
                format.
            contract_settlement_ts (int): Contract's settlement date in UNIX
                timestamp format.
            contract_delivery_ts (int): Contract's delivery date in UNIX
                timestamp format.

        Raises:
            AttributeError: If 'contract_data' is missing a field needed for
                the contract deployment.
        """
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
        """ Configure Ethereum address to be used for contract deployment.

        Args:
             public_key (str): Ethereum address to use for contract deployment.

        Raises:
            ValueError: If the given address is not a valid Ethereum address.
        """
        self.default_account = self.validate_to_checksum(public_key)

    def import_account(self, private_key, passphrase, as_default=True):
        """ Import account to the Ethereum node to sign contract deployment.

        Args:
            private_key (str): Ethereum private key to import to the configured
                node.
            passphrase (str): Passphrase used to protect the private_key.
            as_default (bool): If True the imported account will be set as the
                default account used to deploy the contract.

        Returns:
            str: The corresponding public key, that is the Ethereum address
                 matching to the given private key.

        Raises:
            ValueError: If the corresponding public address is not a valid
                Ethereum address.
        """
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
            # TODO Use the flask app's logger instead of print to stdout
            # directly
            print("Can't use the account, deploy won't happen:",
                  default_account)
            return None

        if as_default:
            self.default_account = self.validate_to_checksum(public_key)

        return public_key

    def deploy_compiled(self, abi, bytecode):
        """ Deploy the given contract's ABI and Bytecode.

        Note this function blocks the thread, since it waits for the block
        containing the deployment transaction to be mined befor returning. So
        is not a good idea to call it in the main thread.

        Args:
            abi (str): The contract's ABI to deploy.
            bytecode (str): The contract's Bytecode to deploy.

        Raises:
            ValueError: If the contract data or default account neede for
                deployment have not been set. Need to call
                "set_deployment_account" and "set_contract_data" functions
                first.

        Returns:
            str: The deployed contract's Ethereum address.
        """
        if not (self.default_account and self.contract_data):
            raise ValueError(
                'Set up account and contract data before deploying')

        # Instantiate and deploy contract
        contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)

        # TODO Can use this to estimate gas and log that out
        # https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.estimateGas

        tx_hash = contract.constructor(
            self.contract_data['customer_address'],
            self.contract_data['oracle_address'],
            self.contract_data['contract_amount'],
            self.contract_data['oracle_fee'], self.contract_data['lcurl'],
            self.contract_data['lchash'],
            self.contract_data['contract_settlement_ts'],
            self.contract_data['contract_duedate_ts'],
            self.contract_data['contract_delivery_ts']).transact({
                'from':
                self.default_account
            })

        # TODO Return 'tx_hash' instead so other process could monitor the receipt
        return tx_hash

        # Get tx receipt to get contract address
        # tx_receipt = self.w3.eth.waitForTransactionReceipt(
        #     tx_hash, timeout=300)

        # print('\n\n======= TX RECEIPT ========')
        # print(pprint.pformat(tx_receipt))

        # return tx_receipt['contractAddress']  # Return contract address

    def deploy(self, contract_name, contract_source_code):
        """ Deploy the contract given the name and the source code.

        Note this function blocks the thread, since it waits for the block
        containing the deployment transaction to be mined befor returning. So
        is not a good idea to call it in the main thread.

        Args:
            contract_name (str): The contract's name.
            contract_source_code (str): The contract's plain source code.

        Raises:
            ValueError: If the contract data or default account neede for
                deployment have not been set. Need to call
                "set_deployment_account" and "set_contract_data" functions
                first.

        Returns:
            str: The deployed contract's Ethereum address.
        """
        # TODO Use an extra flag parameter to know if should loop after
        # TimeExhausted is raised, so it can wait infinitely for the
        # transaction to be mined?

        if not (self.default_account and self.contract_data):
            raise ValueError(
                'Set up account and contract data before deploying')

        compiled_sol = solc.compile_source(contract_source_code, optimize=True)
        contract_interface = compiled_sol['<stdin>:' + contract_name]

        return self.deploy_compiled(contract_interface['abi'],
                                    contract_interface['bin'])
