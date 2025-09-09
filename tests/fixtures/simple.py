# Simple test file for BEC completions and signatures
import numpy as np


# Test completion at various positions
def test_completions():
    # Line for testing BEC client completions - cursor after 'bec.'
    result = bec.device_manager

    # Line for testing device completions - cursor after 'dev.'
    motor = dev.samx

    # Line for testing scan completions - cursor after 'scans.'
    scan_result = scans.line_scan

    # Line for testing movement function signatures - cursor inside parentheses
    mv(motor, 10)
    mvr(motor, 5)
    umv(motor, 20)
    umvr(motor, -5)

    # Line for testing numpy completions - cursor after 'np.'
    array = np.array([1, 2, 3])

    return result
