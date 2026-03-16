from flask import Flask
from app.config import Config
from app.extensions import db, login_manager, migrate, mail
from app.routes.auth import auth
from app.routes.managerDashboard import manager
from app.routes.engineer import engineer
from app.routes.bugDashboard import bug

def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    db.init_app(flask_app)
    login_manager.init_app(flask_app)
    migrate.init_app(flask_app, db)
    mail.init_app(flask_app)

    login_manager.login_view = "auth.login_page"

    import app.auth_utils  # <-- important

    flask_app.register_blueprint(auth)
    flask_app.register_blueprint(manager)
    flask_app.register_blueprint(engineer)
    flask_app.register_blueprint(bug)

    return flask_app