"""
Tone Detection API using Flask
"""
import os
from dotenv import load_dotenv
from flask import Flask
from flask_smorest import Api
from resources.tone import blp as ToneBlueprint

load_dotenv()

def create_app():
    """
    Create and configure the Flask application.
    """
    app = Flask(__name__)
    app.config["API_TITLE"] = "Tone Detection API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config[
        "OPENAPI_SWAGGER_UI_URL"
    ] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    api = Api(app)


    api.register_blueprint(ToneBlueprint)

    return app

if __name__ == "__main__":
    f_app = create_app()
    f_app.run(port=8080, debug=False)
