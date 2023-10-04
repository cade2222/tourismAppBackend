from flask import Flask

app = application = Flask(__name__)


@app.route('/')
def hello():
    return '<h1>Hello, World!</h1>'


@app.route('/apicall')
def apicall():
    return {"user" : "David"}