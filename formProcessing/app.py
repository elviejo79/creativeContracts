from flask import Flask
from flask import render_template
from flask import request
import pprint
from weasyprint import HTML
import hashlib

app = Flask(__name__,static_url_path='/static')


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
    contract_filename = hashlib.sha256(contract_in_pdf).hexdigest()
    #contract_filename = 'hola_mundo'
    contract_uri = "/tmp/%s.pdf" % contract_filename
    filehandler = open(contract_uri, "wb")
    filehandler.write(contract_in_pdf)
    return contract_uri
