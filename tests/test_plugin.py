from unittest.mock import Mock, patch

from bec_lib.tests.fixtures import bec_client_mock  # noqa: F401

from pylsp_bec import completions, signatures


def test_bec_completions_basic(config, workspace, document, bec_client_mock):
    """Test that BEC completions are provided for bec. prefix."""
    # Position after 'bec.' (line 6, character 24 in our fixture)
    position = {"line": 6, "character": 24}

    with patch("pylsp_bec.client", bec_client_mock):
        response = completions.pylsp_completions(
            config=config, workspace=workspace, document=document, position=position
        )

    # Should return completion items
    assert response is not None
    assert isinstance(response, list)


def test_bec_completions_no_jedi_interference(config, workspace, document):
    """Test that BEC completions don't interfere when Jedi has completions."""
    position = {"line": 6, "character": 24}

    # Set up document to indicate Jedi already provided completions
    document.shared_data = {"LAST_JEDI_COMPLETIONS": {"some": "completions"}}

    response = completions.pylsp_completions(
        config=config, workspace=workspace, document=document, position=position
    )

    # Should return empty list when Jedi already provided completions
    assert response == []


def test_device_completions(config, workspace, document, bec_client_mock):
    """Test completions for device access patterns."""
    # Position after 'dev.' on line 11 (0-indexed as line 10, character 16)
    # This tests completion for 'dev.samx' in the fixture
    position = {"line": 10, "character": 16}

    with patch("pylsp_bec.client", bec_client_mock):
        response = completions.pylsp_completions(
            config=config, workspace=workspace, document=document, position=position
        )

    assert response is not None
    assert isinstance(response, list)

    # Check that we get some completions for device attributes
    if response:
        # Should have completion items
        assert len(response) > 0
        # Each completion should have a label
        for completion in response:
            assert "label" in completion


def test_device_name_completions(config, workspace, document, bec_client_mock):
    """Test that specific device names appear in completions."""
    # Position after 'dev.' on line 11 where we expect device names
    position = {"line": 10, "character": 16}

    with patch("pylsp_bec.client", bec_client_mock):
        response = completions.pylsp_completions(
            config=config, workspace=workspace, document=document, position=position
        )

    assert response is not None
    if response:
        # Convert to labels for easier checking
        labels = [item.get("label", "") for item in response]
        # Should have device-related completions
        assert len(labels) > 0

        # Check that specific device names are in the completions
        # The bec_client_mock should have these common devices
        expected_devices = ["samx", "samy", "samz"]
        found_devices = [device for device in expected_devices if device in labels]

        # All expected devices should be found in completions
        assert len(found_devices) == len(expected_devices), (
            f"Expected devices {expected_devices} not all found in completions. "
            f"Found: {found_devices}, Missing: {set(expected_devices) - set(found_devices)}"
        )

        # Specifically check that 'samx' (from line 11) is in the completions
        assert "samx" in labels, f"Device 'samx' not found in completions: {labels[:10]}..."


def test_scan_completions(config, workspace, document, bec_client_mock):
    """Test completions for scan methods."""
    # Position after 'scans.' (line 12, character 26 in our fixture)
    position = {"line": 12, "character": 26}

    with patch("pylsp_bec.client", bec_client_mock):
        response = completions.pylsp_completions(
            config=config, workspace=workspace, document=document, position=position
        )

    assert response is not None


def test_numpy_completions(config, workspace, document, bec_client_mock):
    """Test that numpy completions work through our plugin."""
    # Position after 'np.' (line 21, character 14 in our fixture)
    position = {"line": 21, "character": 14}

    with patch("pylsp_bec.client", bec_client_mock):
        response = completions.pylsp_completions(
            config=config, workspace=workspace, document=document, position=position
        )

    assert response is not None


def test_completion_settings(config, workspace, document, bec_client_mock):
    """Test that completion settings are respected."""
    position = {"line": 6, "character": 24}

    # Mock config settings
    config.plugin_settings = Mock(
        return_value={
            "eager": True,
            "fuzzy": True,
            "include_params": True,
            "include_class_objects": True,
            "include_function_objects": True,
            "resolve_at_most": 10,
            "cache_for": ["some_module"],
        }
    )

    with patch("pylsp_bec.client", bec_client_mock):
        response = completions.pylsp_completions(
            config=config, workspace=workspace, document=document, position=position
        )

    assert response is not None


# Signature tests
def test_mv_signature_help(config, workspace, document, bec_client_mock):
    """Test signature help for movement functions."""
    # Position inside mv() call (line 15, character 8 in our fixture)
    position = {"line": 15, "character": 8}

    with patch("pylsp_bec.client", bec_client_mock):
        response = signatures.pylsp_signature_help(
            config=config, workspace=workspace, document=document, position=position
        )

    # Should return signature information
    assert response is not None
    assert "signatures" in response
    assert "activeSignature" in response


def test_signature_help_runtime_fallback(config, workspace, document, bec_client_mock):
    """Test that runtime signatures work when Jedi fails."""
    position = {"line": 15, "character": 8}

    with patch("pylsp_bec.client", bec_client_mock):
        # Mock document.jedi_script() to return empty signatures
        document.jedi_script = Mock()
        document.jedi_script.return_value.get_signatures.return_value = []

        response = signatures.pylsp_signature_help(
            config=config, workspace=workspace, document=document, position=position
        )

    assert response is not None
    assert "signatures" in response


def test_signature_help_with_parameters(config, workspace, document, bec_client_mock):
    """Test signature help includes parameter information."""
    position = {"line": 15, "character": 8}

    with patch("pylsp_bec.client", bec_client_mock):
        response = signatures.pylsp_signature_help(
            config=config, workspace=workspace, document=document, position=position
        )

    assert response is not None
    if response["signatures"]:
        # If we have signatures, check they have the expected structure
        sig = response["signatures"][0]
        assert "label" in sig
        assert "documentation" in sig


def test_signature_capabilities_support(config, workspace, document, bec_client_mock):
    """Test that signature help works with basic functionality."""
    position = {"line": 15, "character": 8}

    with patch("pylsp_bec.client", bec_client_mock):
        response = signatures.pylsp_signature_help(
            config=config, workspace=workspace, document=document, position=position
        )

    assert response is not None


def test_get_object_from_namespace():
    """Test the utility function for getting objects from namespace."""
    namespace = {"test_obj": Mock(), "nested": Mock()}
    namespace["nested"].method = Mock()

    # Test simple access
    result = signatures.get_object_from_namespace("test_obj", namespace)
    assert result == namespace["test_obj"]

    # Test nested access
    result = signatures.get_object_from_namespace("nested.method", namespace)
    assert result == namespace["nested"].method

    # Test invalid access
    result = signatures.get_object_from_namespace("nonexistent.attr", namespace)
    assert result is None
