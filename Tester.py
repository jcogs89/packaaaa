import zlib
import sys, getopt

#This file is for testing the resultant encrypted/compressed file from the Packer

def main(argv):
    inputfile = ''
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print('test.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
    
    compressed_data = open(inputfile, 'rb').read()
    decompressed_data = zlib.decompress(compressed_data)
    
    f = open(outputfile, 'wb')
    f.write(decompressed_data)
    f.close()

if __name__ == "__main__":
   main(sys.argv[1:])