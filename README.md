# packaaaa

This code repository is the code for the Packer portion of the CYSE 492 Senior Design Project (Lockheed Martin Packer/Loader)

The follow dependencies are required to build (available in requirements.txt):
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

Usage

1. Within the same directory as Packer.py, create a folder called `static`
2. Within this `static` folder, create a folder for a loader (name of folder should be ID of loader), and have a .txt file with the name of the loader (authorize the loader by placing its ID in authorized-ids.txt). 
3. Within this loader folder, any folders placed within will serve as payload folders. 2 files, details.txt and `secret-key` should be present. A secret key file can be generated by running ./Packer.py -g, help for this can be accessed with the -h flag.
4. In each payload folder, place any executables/files that should be sent to the loader. The order in which they are sent is determined by an alphabetical sort, so name your files appropriately. Accompanying each executable/file can be 2 additional files for argv and envp arguments. For example, if you have "a.exe", you may create "a.argv" and "a.envp".
5. Additionally, a similar file "a.flags" may be provided to issue additional instructions to the Loader regarding the particular executable/file

Possible boolean flags (1 is set, default is 0)
    0x1 - Hold execution of next execution til this one finishes (default is parallel execution)
    0x2 - Write to disk if non exe, (default is no)

6. A reserved payload named instructions will be in each loader's id folder, within this, a normal text file contains the names of each payload you want to send to the loader the next time it checks in

Format:

;payload payload payload
;payload
;payload payload

Multiple payloads can be sent to a Loader by delimiting them with a space

Loaders keep track of the number of sent instructions, so instructions may not be deleted unless the final instruction is reset

To prevent the instructions file from growing too large, a "reset" command is implemented that resets all active loader sequence numbers to the first line

7. A log is kept in the same directory as the Packer, it is important to create the ./logs/ folder before first use. Multiple instances of the same Loader can be kept track of in the log by providing a uid field in the http request. Accepted characters: a-z A-Z 0-9

Logs are kept in the current dir under /logs/ and the columns are organized in the following manner
datetime | log level | loaderID | payloadRequested | UID 

To create final executable: https://pyinstaller.readthedocs.io/en/stable/usage.html
