from flask import Flask, jsonify, request, render_template

app = Flask(__name__)
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')