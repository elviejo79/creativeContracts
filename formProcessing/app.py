import os
import json
import pprint
from flask import Flask
from flask import render_template
from flask import request
from utils import make_celery, generate_pdf

app = Flask(__name__, static_url_path='/static')
app.config.update(
    # Celery will use the broker as a task queue
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379',

    # Options to connect to the Ethereum node used for deployment
    GETH_NODE_URI=os.getenv('GETH_NODE_URI', 'http://localhost:8565'),
    GETH_USES_IPC=False,
    GETH_USES_POA=False,

    # User account used to sign and deploy the contract
    ETH_USER_PKEY=os.environ['ETH_USER_PKEY'],
    ETH_USER_PASS=os.environ['ETH_USER_PASS'],

    # Contract name and file path to the contract's solidity file
    CREATIVE_CONTRACT_NAME=os.getenv('CC_NAME', 'CreativeContract'),
    CREATIVE_CONTRACT_FILE=os.getenv('CC_FILE',
                                     '../contracts/CreativeContract.sol'))

celery = make_celery(app)



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
    """ Creates a contract in PDF and deploys a SmartContract to EVM.

    Request Data:
        amount: Amount to pay for the service.
        settlementDate: Date of settlement of the contract.
        ETHCliente: ETH Address of the customer requiring the service.
        customerName: Name of the business.
        eventName: Name of the event
        customerTelephone: Self explanatory.
        customerHomeAddress: Self explanatory.
        eventDetails: Self explanatory.
        eventType: Categorization of the event.
        Cliente: Customer name receiving the service.
        email: Customer email.
    """
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
