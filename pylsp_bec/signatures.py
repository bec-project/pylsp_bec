from functools import reduce
from inspect import _ParameterKind

import jedi
from jedi.api import helpers
from pylsp import _utils, hookimpl, uris
from pylsp.plugins.signature import _param_docs

from pylsp_bec.utils import get_namespace


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

    namespace = get_namespace()
    code_position = _utils.position_to_jedi_linecolumn(document, position)

    script = jedi.Interpreter(
        document.source, namespaces=[namespace], path=uris.to_fs_path(document.uri)
    )
    pos = code_position["line"], code_position["column"]

    call_details = helpers.get_signature_details(script._module_node, pos)
    if call_details is None:
        return sig_info
    pos = call_details.bracket_leaf.start_pos

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

    # if we have *args in the signature, the index of the active parameter should be set to
    # the arg index if we don't have a keyword argument

    # First, get the index of the args entry of the signature if it exists
    args_index = next((i for i, p in enumerate(sig_items.params) if p.name == "args"), None)
    filled_kwargs = [
        name for _, name, complete in call_details._list_arguments() if name and complete
    ]

    if call_details.keyword_name_str is None:
        if args_index is not None:
            sig_info["activeParameter"] = min(call_details.index, args_index)
        else:
            sig_info["activeParameter"] = min(call_details.index, len(sig_items.params))
        if filled_kwargs:
            filled_set = set(filled_kwargs)
            param_names = [
                p.name for p in sig_items.params if p.kind == _ParameterKind.KEYWORD_ONLY
            ]
            remaining_params = [p for p in param_names if p not in filled_set]
            if remaining_params:
                next_param = remaining_params[0]
                for i, p in enumerate(sig_items.params):
                    if p.name == next_param:
                        sig_info["activeParameter"] = i
                        break
        return sig_info

    for i, p in enumerate(sig_items.params):
        if p.name == call_details.keyword_name_str:
            sig_info["activeParameter"] = i
            break
    return sig_info
