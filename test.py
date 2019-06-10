from flask import Flask
app = Flask(__name__)



@app.route('/')
def hello_world():
    return "yo"

if __name__ == '__main__':
    app.run(port=80, debug=True)
