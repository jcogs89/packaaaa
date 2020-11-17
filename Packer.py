from flask import Flask, request, jsonify, current_app
import os

from flask.helpers import send_file
app = Flask(__name__)

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route('/')
def hello_world():
    raise InvalidUsage(message='This is a restricted server. Your IP has been logged.', status_code=403)

#This is the api used when the loader 
@app.route('/api/<id>', methods=['GET'])
def mainpacker(id):
    with current_app.open_resource('static/authorized-ids.txt') as f:
        authorized = False
        for ids in f:
            ids = ids.strip() #remove \n
            if id == ids.decode():
                authorized = True
                break
    if not authorized:
        raise InvalidUsage(message='This is a restricted server. Your IP has been logged.', status_code=403)
    

    try:
        return send_file('static/' + id, attachment_filename=id)
    except Exception as e:
        return str(e)

app.run()
#app.run(host = "0.0.0.0", port = 25566)