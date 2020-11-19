from flask import Flask, request, jsonify, current_app
import os
import io
import zlib

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
    
    available_payloads = []
    for (_, dirnames, _) in os.walk('static/' + id):
        available_payloads.extend(dirnames)
    
    #choose a payload or get available payloads
    if request.args.get('send', '') in available_payloads and request.args.get('send', '') != '':
        try:
            fileblob = bytearray(b'')
            file_meta = "meta-"
            for (root, _, filenames) in os.walk('static/' + id + '/' + request.args.get('send')):
                for filename in filenames:
                    current_file = open(os.path.join(root, filename), 'rb').read()
                    compressed_file = zlib.compress(current_file, zlib.Z_BEST_COMPRESSION)
                    o_filesize = len(current_file)
                    c_filesize = len(compressed_file)
                    file_meta = file_meta + str(o_filesize) + "." + str(c_filesize) + "-"
                    fileblob.extend(compressed_file)
            
            #we should send the metadata in the filename
            return send_file(io.BytesIO(fileblob), as_attachment=True, attachment_filename=file_meta)
        except Exception as e:
            return str(e)
    else:
        return jsonify(available_payloads)

app.run()
#app.run(host = "0.0.0.0", port = 25566)