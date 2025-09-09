from functools import reduce

import jedi
import numpy as np
from bec_ipython_client.high_level_interfaces.bec_hli import mv, mvr, umv, umvr
from jedi.api import helpers
from pylsp import _utils, hookimpl, uris
from pylsp.plugins.signature import _param_docs

from pylsp_bec import client


@hookimpl(tryfirst=True)
def pylsp_signature_help(config, workspace, document, position):
    code_position = _utils.position_to_jedi_linecolumn(document, position)
    signatures = document.jedi_script().get_signatures(**code_position)

    if not signatures:
        return _get_runtime_signatures(document, position)

    signature_capabilities = config.capabilities.get("textDocument", {}).get("signatureHelp", {})
    signature_information_support = signature_capabilities.get("signatureInformation", {})
    supported_markup_kinds = signature_information_support.get("documentationFormat", ["markdown"])
    preferred_markup_kind = _utils.choose_markup_kind(supported_markup_kinds)

    s = signatures[0]

    docstring = s.docstring()

    # Docstring contains one or more lines of signature, followed by empty line, followed by docstring
    function_sig_lines = (docstring.split("\n\n") or [""])[0].splitlines()
    function_sig = " ".join([line.strip() for line in function_sig_lines])
    sig = {
        "label": function_sig,
        "documentation": _utils.format_docstring(
            s.docstring(raw=True), markup_kind=preferred_markup_kind
        ),
    }

    # If there are params, add those
    if s.params:
        sig["parameters"] = [
            {
                "label": p.name,
                "documentation": _utils.format_docstring(
                    _param_docs(docstring, p.name), markup_kind=preferred_markup_kind
                ),
            }
            for p in s.params
        ]

    # We only return a single signature because Python doesn't allow overloading
    sig_info = {"signatures": [sig], "activeSignature": 0}

    if s.index is not None and s.params:
        # Then we know which parameter we're looking at
        sig_info["activeParameter"] = s.index

    return sig_info


def get_object_from_namespace(expr: str, namespace: dict):
    """
    Given an expression like 'scans.acquire', traverse the namespace
    and return the actual object (method, function, etc.)
    """
    parts = expr.split(".")
    try:
        obj = reduce(getattr, parts[1:], namespace[parts[0]])
        return obj
    except Exception:
        return None


def _get_runtime_signatures(document, position):
    sig_info = {"signatures": [], "activeSignature": 0}

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
    code_position = _utils.position_to_jedi_linecolumn(document, position)
    script = jedi.Interpreter(document.source, [namespace], path=uris.to_fs_path(document.uri))
    pos = code_position["line"], code_position["column"]

    call_details = helpers.get_signature_details(script._module_node, pos)
    if call_details is None:
        return sig_info

    pos = code_position["line"], code_position["column"] - 1
    items = script.goto(*pos)
    if not items:
        return sig_info
    sig_items = items[0].get_signatures()[0]
    docstring = sig_items.docstring()
    function_sig_lines = (docstring.split("\n\n") or [""])[0].splitlines()
    function_sig = " ".join([line.strip() for line in function_sig_lines])
    if function_sig.startswith("<lambda>"):
        function_sig = function_sig.replace("<lambda>", items[0].name)
    sig = {
        "label": function_sig,
        "documentation": _utils.format_docstring(
            sig_items.docstring(raw=True), markup_kind="markdown"
        ),
    }
    if sig_items.params:
        sig["parameters"] = [
            {
                "label": p.name,
                "documentation": _utils.format_docstring(
                    _param_docs(docstring, p.name), markup_kind="markdown"
                ),
            }
            for p in sig_items.params
        ]
    sig_info["signatures"].append(sig)
    sig_info["activeSignature"] = 0
    return sig_info
