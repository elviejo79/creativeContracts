import os
from flask import Flask
from flask import render_template
from flask import request
import pprint
from weasyprint import HTML
import hashlib
import json

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
    contract_in_html = render_template('CONTRATO.html', e=event_data)
    contract_in_pdf = HTML(string=contract_in_html).write_pdf()
    contract_hash = hashlib.sha256(contract_in_pdf).hexdigest()
    # contract_filename = 'hola_mundo'
    contract_path = "./static/contratos/%s.pdf" % contract_hash
    filehandler = open(contract_path, "wb")
    filehandler.write(contract_in_pdf)
    contract_info = {
        'legalContractUrl':
        "%sstatic/contratos/%s.pdf" % (request.host_url, contract_hash),
        'legalContractHash':
        contract_hash
    }
    # TODO Create async function that waits for the contract address and
    #      doesn't stop flask, pass the contract_hash to identify the related PDF.
    # Use Celery: https://stackoverflow.com/a/31867108/2948807
    return json.dumps(contract_info)


# TODO Create another controller for receiving the address
#      This controller should generate a new PDF with the contract address in a
#      QR and save it into a folder with the same HASH name of the old PDF. So
#      wix can search for them in a specified link.
