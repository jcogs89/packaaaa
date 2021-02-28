# packaaaa

This code repository is the code for the Packer portion of the CYSE 492 Senior Design Project (Lockheed Martin Packer/Loader)

The follow dependencies are required to build:
```
flask 
pynacl 
pyopenssl 
requests
pysimplegui
config-with-yaml
numpy
```

To run
```
python Packer.py
```

Current Functionality:

* Able to send files to a requesting program
* Able to be run in adhoc https mode
* Able to compress files
* Able to encrypt compressed file
* Able to combine multiple encrypted, compressed files into a blob
* Blob metadata is written in the filename
* Contains a tester to test the blob decompression and decryption

todo:
Authenticate usage of api

To create final executable: https://pyinstaller.readthedocs.io/en/stable/usage.html
