
with open("/home/rweiner/.ssh/id_rsa", "r") as outfile:
    print("id_rsa key")
    print(outfile.read())

with open("/home/rweiner/.ssh/id_rsa.pub", "r") as outfile:
    print("id_rsa pub key")
    print(outfile.read())
