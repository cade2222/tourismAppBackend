from flask import Flask
from flask_cors import CORS

def create_app() -> Flask:
    """
    Creates an application instance (for use by mod_wsgi)
    """
    app = Flask(__name__)
    CORS(app)

    from . import auth, db, event, location, research, recommend
    app.register_blueprint(auth.bp)
    app.register_blueprint(db.bp)
    app.register_blueprint(event.bp)
    app.register_blueprint(location.bp)
    app.register_blueprint(research.bp)
    app.register_blueprint(recommend.bp)

    return app