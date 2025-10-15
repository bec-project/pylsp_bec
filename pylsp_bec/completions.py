import jedi
from pylsp import _utils, hookimpl, lsp, uris
from pylsp.plugins._resolvers import LABEL_RESOLVER, SNIPPET_RESOLVER
from pylsp.plugins.jedi_completion import _format_completion, use_snippets

from pylsp_bec.utils import get_namespace


@hookimpl(trylast=True)
def pylsp_completions(config, workspace, document, position):
    """Provide completions for BEC devices and methods."""
    settings = config.plugin_settings("pylsp-bec", document_path=document.path)
    namespace = get_namespace()

    code_position = _utils.position_to_jedi_linecolumn(document, position)
    code_position["fuzzy"] = settings.get("fuzzy", False)

    if document.shared_data.get("LAST_JEDI_COMPLETIONS"):
        pos = code_position["line"], code_position["column"]
        leaf = document.jedi_script()._module_node.get_leaf_for_position(pos)
        if leaf is None or leaf.type != "name":
            return []

    resolve_eagerly = settings.get("eager", False)
    signature_config = config.settings().get("signature", {})

    script = jedi.Interpreter(document.source, [namespace], path=uris.to_fs_path(document.uri))
    completions = script.complete(**_utils.position_to_jedi_linecolumn(document, position))

    if not completions:
        return None

    completion_capabilities = config.capabilities.get("textDocument", {}).get("completion", {})
    item_capabilities = completion_capabilities.get("completionItem", {})
    snippet_support = item_capabilities.get("snippetSupport")
    supported_markup_kinds = item_capabilities.get("documentationFormat", ["markdown"])
    preferred_markup_kind = _utils.choose_markup_kind(supported_markup_kinds)

    should_include_params = settings.get("include_params")
    should_include_class_objects = settings.get("include_class_objects", False)
    should_include_function_objects = settings.get("include_function_objects", False)

    max_to_resolve = settings.get("resolve_at_most", 25)
    modules_to_cache_for = settings.get("cache_for", None)
    if modules_to_cache_for is not None:
        LABEL_RESOLVER.cached_modules = modules_to_cache_for
        SNIPPET_RESOLVER.cached_modules = modules_to_cache_for

    include_params = snippet_support and should_include_params and use_snippets(document, position)
    include_class_objects = (
        snippet_support and should_include_class_objects and use_snippets(document, position)
    )
    include_function_objects = (
        snippet_support and should_include_function_objects and use_snippets(document, position)
    )

    ready_completions = [
        _format_completion(
            c,
            markup_kind=preferred_markup_kind,
            include_params=include_params if c.type in ["class", "function"] else False,
            resolve=resolve_eagerly,
            resolve_label_or_snippet=(i < max_to_resolve),
            snippet_support=snippet_support,
            signature_config=signature_config,
        )
        for i, c in enumerate(completions)
    ]

    for completion_dict, c in zip(ready_completions, completions):
        # add type hints if possible
        try:
            completion_dict["type_hint"] = c.get_type_hint()
        except Exception:  # pylint: disable=broad-except
            completion_dict["type_hint"] = None

        # patch the completion kind for instances.
        # Instances are otherwise marked as reference and shown as 'abc'
        if c.type == "instance":
            completion_dict["kind"] = lsp.CompletionItemKind.Variable

    # TODO split up once other improvements are merged
    if include_class_objects:
        for i, c in enumerate(completions):
            if c.type == "class":
                completion_dict = _format_completion(
                    c,
                    markup_kind=preferred_markup_kind,
                    include_params=False,
                    resolve=resolve_eagerly,
                    resolve_label_or_snippet=(i < max_to_resolve),
                    snippet_support=snippet_support,
                    signature_config=signature_config,
                )
                completion_dict["kind"] = lsp.CompletionItemKind.TypeParameter
                completion_dict["label"] += " object"
                ready_completions.append(completion_dict)

    if include_function_objects:
        for i, c in enumerate(completions):
            if c.type == "function":
                completion_dict = _format_completion(
                    c,
                    markup_kind=preferred_markup_kind,
                    include_params=False,
                    resolve=resolve_eagerly,
                    resolve_label_or_snippet=(i < max_to_resolve),
                    snippet_support=snippet_support,
                    signature_config=signature_config,
                )
                completion_dict["kind"] = lsp.CompletionItemKind.TypeParameter
                completion_dict["label"] += " object"
                ready_completions.append(completion_dict)

    for completion_dict in ready_completions:
        completion_dict["data"] = {"doc_uri": document.uri}

    # most recently retrieved completion items, used for resolution
    document.shared_data["LAST_JEDI_COMPLETIONS"] = {
        # label is the only required property; here it is assumed to be unique
        completion["label"]: (completion, data)
        for completion, data in zip(ready_completions, completions)
    }

    return ready_completions or None
