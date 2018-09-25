import sys
import solc
from web3 import Web3, HTTPProvider, IPCProvider
from eth_account import Account
from web3.middleware import geth_poa_middleware

# web3.py instance
ethereum_node = 'http://localhost:8545'
ethereum_ipc = '/Users/antares/Library/Ethereum/geth.ipc'
# provider = HTTPProvider(ethereum_node)
provider = IPCProvider(ethereum_ipc)
w3 = Web3(provider)
w3.middleware_stack.inject(geth_poa_middleware, layer=0)  # Needed for PoA


def main(contract_source_code, private_key, passphrase):
    compiled_sol = solc.compile_source(contract_source_code, optimize=True)
    contract_interface = compiled_sol['<stdin>:CreativeContract']

    # Check if address exists
    public_key = Account.privateKeyToAccount(private_key).address

    if public_key not in w3.eth.accounts:
        # Add a sample wallet with ropsten funds
        w3.personal.importRawKey(private_key, passphrase)

    # Unlock wallet to allow outgoing transactions
    default_account = public_key
    print('Will use account: ', default_account)
    is_unlocked = w3.personal.unlockAccount(default_account, passphrase)
    if not is_unlocked:
        print("Can't use the account, deploy won't happen:", default_account)
        exit()

    # Instantiate and deploy contract
    contract = w3.eth.contract(
        abi=contract_interface['abi'], bytecode=contract_interface['bin'])

    # Constructor arguments
    customer_address = Web3.toChecksumAddress(
        "0x14723a09acff6d2a60dcdf7aa4aff308fddc160c")
    oracle_address = Web3.toChecksumAddress(
        "0x4b0897b0513fdc7c541b6d9d7e929c4e5364d2db")
    contract_amount = 10
    oracle_fee = 1
    lcurl = "http://www.creativecontract.org"
    lchash = "B221D9DBB083A7F33428D7C2A3C3198AE925614D70210E28716CCAA7CD4DDB79"
    contract_duedate_ts = 1544779800000
    contract_settlement_ts = 1545384600000
    contract_delivery_ts = 1546384600000

    tx_hash = contract.constructor(customer_address, oracle_address,
                                   contract_amount, oracle_fee, lcurl, lchash,
                                   contract_settlement_ts, contract_duedate_ts,
                                   contract_delivery_ts).transact({
                                       'from':
                                       default_account
                                   })

    # Get tx receipt to get contract address
    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    # TODO: TypeError: 'NoneType' object is not subscriptable: contract_address = tx_receipt['contractAddress']
    contract_address = tx_receipt['contractAddress']

    # Contract instance in concise mode
    print('Contract address is: ')
    print(contract_address)
    # abi = contract_interface['abi']
    # contract_instance = w3.eth.contract(
    #     address=contract_address,
    #     abi=abi,
    #     ContractFactoryClass=ConciseContract)

    # Getters + Setters for web3.eth.contract object


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(
            'Usage: python deployc.py CreativeContract.sol <private key> <passphrase>'
        )
        exit()

    contract_file_code = sys.argv[1]
    private_key = sys.argv[2]
    passphrase = sys.argv[3]

    # Get source code from solidity file
    source_code = ''
    with open(contract_file_code, 'r') as f:
        source_code = ''.join(f.readlines())

    # Get private key from keystore file
    # private_key = ''
    # with open(user_keystore_file, 'r') as keyfile:
    #     encrypted_key = keyfile.read()
    #     private_key = w3.eth.account.decrypt(encrypted_key,
    #                                          user_keystore_passphrase)

    main(source_code, private_key, passphrase)
