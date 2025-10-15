import numpy as np
from bec_ipython_client.high_level_interfaces.bec_hli import mv, mvr, umv, umvr

from pylsp_bec import client


def get_namespace() -> dict:
    """Get the namespace dictionary used for completions and signatures."""
    namespace = {
        "bec": client,
        "np": np,
        "dev": getattr(client.device_manager, "devices", None),
        "scans": getattr(client, "scans", None),
        "mv": mv,
        "mvr": mvr,
        "umv": umv,
        "umvr": umvr,
    }
    namespace.update(
        {name: obj["cls"] for name, obj in client.macros._update_handler.macros.items()}
    )
    return namespace
