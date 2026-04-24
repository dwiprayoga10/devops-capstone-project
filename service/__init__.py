"""
Package: service
"""
import sys
from flask import Flask
from service import config
from service.common import log_handlers
from flask_talisman import Talisman
from flask_cors import CORS

# Create Flask application
app = Flask(__name__)
app.config.from_object(config)

talisman = Talisman(app)
CORS(app)

# Import for side effects (routes & handlers)
from service import routes, models  # noqa: F401
from service.common import error_handlers, cli_commands  # noqa: F401

# Logging
log_handlers.init_logging(app, "gunicorn.error")

app.logger.info("*" * 70)
app.logger.info("ACCOUNT SERVICE RUNNING".center(70, "*"))
app.logger.info("*" * 70)

try:
    models.init_db(app)
except Exception as error:
    app.logger.critical("%s: Cannot continue", error)
    sys.exit(4)

app.logger.info("Service initialized!")
