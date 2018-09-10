import sys
import solc
from web3 import Web3, HTTPProvider, TestRPCProvider
from web3.contract import ConciseContract


def main():
    contract_source_code = ''.join(sys.stdin.readlines())
    compiled_sol = solc.compile_source(contract_source_code)
    contract_interface = compiled_sol['<stdin>:CreativeContract']

    # web3.py instance
    ropsten_node = 'http://localhost:7545'
    w3 = Web3(HTTPProvider(ropsten_node))

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
                                       w3.eth.accounts[0]
                                   })

    # Get tx receipt to get contract address
    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
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
    main()
