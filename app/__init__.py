import os
from flask import Flask
from flasgger import Swagger
from config import config_map
from app.extensions import db, jwt, ma, limiter, mail, migrate


def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    ma.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    Swagger(app, template={
        'info': {
            'title': 'Customer Support Ticket API',
            'version': '1.0',
            'description': 'REST API for customer support ticket management',
        },
        'securityDefinitions': {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': 'JWT Bearer token. Example: "Bearer <token>"',
            }
        },
    })

    from app.routes.auth import auth_bp
    from app.routes.tickets import tickets_bp
    from app.routes.users import users_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tickets_bp, url_prefix='/api')
    app.register_blueprint(users_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    from app.utils.errors import APIException, handle_api_exception
    app.register_error_handler(APIException, handle_api_exception)

    return app
