#!/usr/bin/python
'''
This file is meant to be a GUI/CLI for the Packer
'''

from tkinter.constants import CENTER
import requests
import nacl.secret
import PySimpleGUI as sg
import config_with_yaml as config
import time
import json
import sys, getopt
from datetime import datetime

help_msg = {
            "help": "Show this menu",
            "authorized": "Show currently authorized loader ids",
            "available": "Show all loaders currently staged with payloads",
            "online": "Show all deployed loader ids",
        }

'''
help
authorized
available
online
details
edit-details
payloads
send
add-auth-id
add-payload
remove-auth-id
remove-payload
'''

def main(argv):
    cfg = config.load("config.yml")
    key = open('cli-secret-key', 'rb').read()
    box = nacl.secret.SecretBox(key)
    auth_data = box.encrypt(b"packer-cli")

    gui_mode = True

    try:
        opts, args = getopt.getopt(argv, "ch", ["cli", "help"])
    except getopt.GetoptError:
      print("interface.py [-c][--cli] [-h][--help] [-l][--launch]")
      sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("interface.py [-c][--cli] [-h][--help]")
            print("Normally opens a python GUI, -c to use command line")
            sys.exit()
        elif opt in ("-c", "--cli"):
            gui_mode = False
            break
    
    #this program should only be used on the same computer as the packer
    if cfg.getPropertyWithDefault("packer.ssl", False):
        uri = "https://127.0.0.1:" + cfg.getPropertyWithDefault("packer.port", "5000") + "/cli/"
    else:
        uri = "http://127.0.0.1:" + cfg.getPropertyWithDefault("packer.port", "5000") + "/cli/"

    retry_limit = cfg.getPropertyWithDefault("cli.retryLimit", 3)
    retry_time = cfg.getPropertyWithDefault("cli.timeBetweenTries", 1000)
    current_try = 1
    print("Attempting to reach Packer at " + uri)
    while current_try < retry_limit + 1:
        try:
            if requests.get(uri + "hello", data=auth_data).status_code == 200:
                print("Successfully contacted Packer")
                break   

        except:
            if current_try == retry_limit:
                print("Connection to Packer timed out, please make sure it is online")
                return
            print("Could not connect to Packer, is it online? (" + str(current_try) + "/" + str(retry_limit) + ")")
            current_try += 1
            time.sleep(retry_time / 1000)

    if gui_mode:
        gui(uri, auth_data)
    else:
        cli(uri, auth_data)

def cli(uri, auth_data):
    return

def gui(uri, auth_data):
    sg.theme('DarkAmber')

    #gui elements start
    #this list is a list of all loaders defined in the static folder
    available_loader_list = [
        [
            sg.Text("Add new loader"),
            sg.In(size=(20, 1), enable_events=True, key="_new_loader_name_"),
            sg.Button("Submit", key="_submit_new_loader_name_")
        ],
        [ 
            sg.Text("Available Loaders")
        ],
        [
            sg.Listbox(
                values=json.loads(requests.get(uri + "available", data=auth_data).content), enable_events=True, size=(40,20), key="_avail_loader_list_"
            )
        ],
        [
            sg.Button("Remove Loader", key="_remove_avail_loader_"),
            sg.Button("Authorize ->", key="_authorize_avail_loader_")
        ],
    ]

    authorized_loader_list = [
        [ 
            sg.Text("Search for loader"),
            sg.In(size=(20, 1), enable_events=True, key="_search_loader_name_"),
            sg.Button("Submit", key="_submit_search_loader_name_")
        ],
        [ 
            sg.Text("Authorized Loaders")
        ],
        [
            sg.Listbox(
                values=json.loads(requests.get(uri + "authorized", data=auth_data).content), enable_events=True, size=(40,20), key="_auth_loader_list_"
            )
        ],
        [
            sg.Button("<- Deauthorize", key="_deauth_loader_")
        ],
    ]
    
    payload_area = [
        [ 
            sg.Text("Search for payload"),
            sg.In(size=(20, 1), enable_events=True, key="_search_payload_name_"),
            sg.Button("Submit", key="_submit_search_payload_name_")
        ],
        [ 
            sg.Text("Available Payloads")
        ],
        [ 
            sg.Listbox(
                values=[], enable_events=True, size=(40,20), key="_avail_payloads_"
            )
        ],
        [ 
            sg.Button("Add Payload", key="_add_payload_"),
            sg.Button("Delete Payload", key="_delete_payload_")
        ]
    ]

    command_area = [
        [ 
            sg.Text("Selected Loader:"),
        ],
        [ 
            sg.Text("n/a", key="_selected_loader_text_", size=(30, 1))
        ],
        [ 
            sg.Text("Selected Payload:")
        ],
        [ 
            sg.Text("n/a", key="_selected_payload_text_", size=(30, 1))
        ],
        [ 
            sg.HSeparator(pad=(0,10))
        ],
        [ 
            sg.Text("Additional Commands")
        ],
        [ 
            sg.Button("Print Loader Details", key="_loader_details_"),
        ],
        [ 
            sg.Button("Edit Loader Details", key="_edit_loader_details_")
        ],
        [ 
            sg.HSeparator(pad=(0,20))
        ],
        [ 
            sg.Button("Send Payload", size=(14,7), key="_send_payload_")
        ]
    ]

    layout = [
        [
                sg.Column(available_loader_list),
                sg.Column(authorized_loader_list),
                sg.VSeparator(),
                sg.Column(payload_area),
                sg.Column(command_area)
        ],
        [
            sg.Output(size=(180,10))
        ]
    ]

    # Create the Window
    window = sg.Window('Packer Interface', layout)
    # Event Loop to process "events" and get the "values" of the inputs

    selected_avail_loader = ""
    selected_auth_loader = ""
    selected_loader = ""

    add_new_loader = ""
    search_loader = ""
    search_payload = ""

    selected_payload = ""

    while True:
        event, values = window.read()
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H:%M:%S)")
        infoPrefix = "[INFO] " + timestampStr + " "

        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        if event == '_avail_loader_list_' and len(values['_avail_loader_list_']):     # if a list item is chosen
            selected_avail_loader = str(values['_avail_loader_list_'][0])
        if event == '_auth_loader_list_' and len(values['_auth_loader_list_']):
            #select loader
            selected_auth_loader = str(values['_auth_loader_list_'][0])
            print(infoPrefix + "Selected Loader: " + selected_auth_loader)
            window['_selected_loader_text_'].update(selected_auth_loader)
            
            #update payload list
            window['_avail_payloads_'].update(json.loads(requests.get(uri + "payloads?id=" + selected_auth_loader, data=auth_data).content))

        if event == '_avail_payloads_' and len(values['_avail_payloads_']):
            selected_payload = str(values['_avail_payloads_'][0])
            print(infoPrefix + "Selected Payload [" + selected_auth_loader +"]: " + selected_payload)
            window['_selected_payload_text_'].update(selected_payload)

        if event == '_loader_details_':
            print(infoPrefix + "Details request for: " + selected_auth_loader)

            

    window.close()


if __name__ == "__main__":
    main(sys.argv[1:])