import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

from routes.estimacion import es
app.register_blueprint(es)

db = SQLAlchemy(app)