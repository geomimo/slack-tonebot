"""
Tone Detection API using Flask
"""
import os
from dotenv import load_dotenv
from flask import Flask
from flask_smorest import Api
from resources.tone import blp as ToneBlueprint

load_dotenv()


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



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))