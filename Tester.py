import zlib
import sys, getopt
import nacl.utils, nacl.secret

#This file is for testing the resultant encrypted/compressed file from the Packer

def main(argv):
    inputfile = ''
    outputfile = ''
    keyfile = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:k:",["ifile=","ofile=","key="])
    except getopt.GetoptError:
        print('test.py -i <inputfile> -o <outputfile> -k <keyfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -i <inputfile> -o <outputfile> -k <keyfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-k", "--kfile"):
            keyfile = arg

    input_data = open(inputfile, 'rb').read()

    key = open(keyfile, 'rb').read()
    box = nacl.secret.SecretBox(key)
    decrypted_data = box.decrypt(input_data)

    decompressed_data = zlib.decompress(decrypted_data)

    f = open(outputfile, 'wb')
    f.write(decompressed_data)
    f.close()

if __name__ == "__main__":
   main(sys.argv[1:])