import atexit

from bec_lib.client import BECClient

client = BECClient(name="pylsp-bec")
client.start()

# Register client shutdown at exit
atexit.register(client.shutdown)
