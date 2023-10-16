from flask import Flask

def create_app() -> Flask:
    """
    Creates an application instance (for use by mod_wsgi)
    """
    app = Flask(__name__)

    from . import auth, db, event, location
    app.register_blueprint(auth.bp)
    app.register_blueprint(db.bp)
    app.register_blueprint(event.bp)
    app.register_blueprint(location.bp)

    return app