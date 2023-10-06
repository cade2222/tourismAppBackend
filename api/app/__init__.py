from flask import Flask

def create_app() -> Flask:
    """
    Creates an application instance (for use by mod_wsgi)
    """
    app = Flask(__name__)
    
    from . import db
    app.before_request(db.connect)
    app.after_request(db.disconnect)

    return app