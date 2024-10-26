from flask import Flask

app = Flask(__name__)


@app.route('/')
def home():
    return "Der Server läuft!"


@app.route('/favicon.ico')
def favicon():
    return '', 204


if __name__ == "__main__":
    app.run(debug=True)
