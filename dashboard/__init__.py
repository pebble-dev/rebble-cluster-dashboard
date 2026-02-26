try:
    import google.auth.exceptions
    try:
        import googleclouddebugger
        googleclouddebugger.enable(module='dashboard')
    except (ImportError, google.auth.exceptions.DefaultCredentialsError):
        print("Couldn't start cloud debugger")
except ImportError:
    print("Couldn't import google exceptions")

from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from rws_common import honeycomb

from .settings import config

from .api import init_app as init_api

app = Flask(__name__)
app.config.update(**config)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

honeycomb.init(app, 'dashboard')

init_api(app)

@app.route('/heartbeat')
@app.route('/dashboard/heartbeat')
def heartbeat():
    return 'ok'

@app.route('/dummy', methods=['GET', 'POST'])
def dummy():
    return jsonify({})
