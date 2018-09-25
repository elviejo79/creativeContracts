import hashlib
from celery import Celery
from weasyprint import HTML
from flask import render_template


def generate_pdf(event_data):
    """ Generate the contract in PDF given the event data.

    Args:
        event_data (dict): Containing the following keys:
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

    Returns:
        str: Hex digest of the SHA256 computed from the generated PDF.
    """
    contract_in_html = render_template('CONTRATO.html', e=event_data)
    contract_in_pdf = HTML(string=contract_in_html).write_pdf()
    contract_hash = hashlib.sha256(contract_in_pdf).hexdigest()
    contract_path = "./static/contratos/%s.pdf" % contract_hash
    filehandler = open(contract_path, "wb")
    filehandler.write(contract_in_pdf)

    return contract_hash


def make_celery(app):
    """ Create an instance of celery configured using Flask app.

    Args:
        app (object): The Flask application object with configurations
                      'CELERY_RESULT_BACKEND' and 'CELERY_BROKER_URL'.

    Returns:
        object: The celery.Celery object instance.
    """
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL'])

    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    return celery
