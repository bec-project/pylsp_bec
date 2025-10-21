from pylsp import hookimpl

from pylsp_bec.utils import client


@hookimpl
def pylsp_workspace_configuration_changed(config, workspace) -> None:
    """
    Handle changes in workspace configuration.

    This function is called whenever the workspace configuration changes.
    It can be used to update internal settings or reconfigure components
    based on the new configuration.

    Args:
        config (dict): The new configuration settings.
        workspace: The workspace instance where the configuration change occurred.
    """

    config = config.plugin_settings("pylsp-bec")
    client.start(config=config.get("service_config", {}))
