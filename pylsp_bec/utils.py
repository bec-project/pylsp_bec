import atexit

import numpy as np
from bec_ipython_client.high_level_interfaces.bec_hli import mv, mvr, umv, umvr
from bec_lib.client import BECClient
from bec_lib.service_config import ServiceConfig


class ClientWrapper:
    """
    A singleton wrapper for the BECClient instance.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClientWrapper, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self._client = None
        atexit.register(self.shutdown)

    def start(self, name="pylsp-bec", config=None):
        config = config or {}
        if self._client is None:
            config = ServiceConfig(**config)
            self._client = BECClient(name=name, config=config)
            self._client.start()
        else:
            config = ServiceConfig(**config)
            if config.config != self._client._service_config.config:
                self._client.shutdown()
                self._client = BECClient(name=name, config=config)
                self._client.start()

    @property
    def client(self):
        return self._client

    def shutdown(self):
        if self._client:
            self._client.shutdown()


client = ClientWrapper()


def get_namespace() -> dict:
    """Get the namespace dictionary used for completions and signatures."""
    if client.client is None:
        return {}
    namespace = {
        "bec": client.client,
        "np": np,
        "dev": getattr(client.client.device_manager, "devices", None),
        "scans": getattr(client.client, "scans", None),
        "mv": mv,
        "mvr": mvr,
        "umv": umv,
        "umvr": umvr,
    }
    namespace.update(
        {name: obj["cls"] for name, obj in client.client.macros._update_handler.macros.items()}
    )
    return namespace
