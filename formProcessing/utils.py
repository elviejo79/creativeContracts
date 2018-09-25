from celery import Celery


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
