import os
import json
import pprint
from dateutil import parser as dateparser
from flask import Flask
from flask import render_template
from flask import request
from weasyprint import HTML
from utils import make_celery, generate_pdf
from smartcontract import SmartContract

app = Flask(__name__, static_url_path='/static')
app.config.update(
    # Celery will use the broker as a task queue
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379',

    # Options to connect to the Ethereum node used for deployment
    GETH_NODE_URI=os.getenv('GETH_NODE_URI', 'http://localhost:8565'),
    GETH_USES_IPC=os.getenv('GETH_USES_IPC', False),
    GETH_USES_POA=os.getenv('GETH_USES_POA', False),

    # User account used to sign and deploy the contract
    ETH_USER_PKEY=os.environ['ETH_USER_PKEY'],
    ETH_USER_PASS=os.environ['ETH_USER_PASS'],

    # Contract name and file path to the contract's solidity file
    CREATIVE_CONTRACT_NAME=os.getenv('CC_NAME', 'CreativeContract'),
    CREATIVE_CONTRACT_FILE=os.getenv('CC_FILE',
                                     '../contracts/CreativeContract.sol'))

celery = make_celery(app)


@celery.task()
def deploy_new_contract(contract_hash, contract_url, event_details):
    sc = SmartContract(celery.conf['GETH_NODE_URI'],
                       celery.conf['GETH_USES_IPC'],
                       celery.conf['GETH_USES_POA'])

    sc.import_account(celery.conf['ETH_USER_PKEY'],
                      celery.conf['ETH_USER_PASS'])

    # TODO: Generate a new PDF with a QR code of the 'contract_address'
    # TODO Some parameters are not in the 'event_data'
    # TODO Validate convert dates

    # Transform dates to unix timestamps
    due_ts = dateparser.parse(event_details['dueDate']).timestamp()
    settlement_ts = dateparser.parse(
        event_details['settlementDate']).timestamp()
    delivery_ts = dateparser.parse(event_details['dateOfDelivery']).timestamp()

    sc.set_contract_data(
        customer_address=event_details['customerAddress'],
        oracle_address=event_details['oracleAddress'],
        contract_amount=int(event_details['amount']),
        oracle_fee=int(event_details['oracleFee']),
        lcurl=contract_url,
        lchash=contract_hash,
        contract_duedate_ts=due_ts,
        contract_settlement_ts=settlement_ts,
        contract_delivery_ts=delivery_ts)

    # Read solidity code
    source_code = ''
    with open(celery.conf['CREATIVE_CONTRACT_FILE'], 'r') as f:
        source_code = ''.join(f.readlines())

    # This will block until transaction is mined (default timeout is 120s)
    contract_address = sc.deploy(celery.conf['CREATIVE_CONTRACT_NAME'],
                                 source_code)

    # PDF Generation
    event_details['ETHContractAddress'] = contract_address

    # TODO Should the 'contract_address' be part of the file name?
    contract_in_html = render_template('CONTRATO.html', e=event_details)
    contract_in_pdf = HTML(string=contract_in_html).write_pdf()
    contract_path = "./static/contratos/%s_deployed.pdf" % contract_hash
    filehandler = open(contract_path, "wb")
    filehandler.write(contract_in_pdf)


@app.route('/')
def index():
    return 'index!'


@app.route('/hello')
def hello_anonymous():
    return 'Hello, World!'


@app.route('/hello/<name>')
def hello(name):
    return render_template('hello_template.html', name=name)


@app.route('/user/<username>')
def show_user_profile(username):
    return 'User %s' % username


@app.route('/post/<int:post_id>')
def show_post(post_id):
    return 'Post %d' % post_id


@app.route('/path/<path:subpath>')
def show_subpath(subpath):
    return 'Subpath %s' % subpath


@app.route('/api/process', methods=['POST'])
def postjson():
    content = request.get_json()
    return pprint.pformat(content)


@app.route('/contrato/new', methods=['POST'])
def contrato_new():
    event_data = request.get_json()

    # PDF Generation
    contract_hash = generate_pdf(event_data)
    contract_url = "%sstatic/contratos/%s.pdf" % (request.host_url,
                                                  contract_hash)

    # Smart Contract Generation
    deploy_new_contract.delay(contract_hash, contract_url, event_data)  # async

    # TODO Should add the expected URL for the post-deployed contract PDF?
    return json.dumps({
        'legalContractUrl': contract_url,
        'legalContractHash': contract_hash
    })
