# pylsp-bec

A Python Language Server plugin that provides enhanced IDE support for BEC (Beamline and Experiment Control) system development.

## Features

- **Smart completions** for BEC devices, scans, and high-level interfaces
- **Signature help** for BEC methods and functions
- **Runtime context awareness** with access to live BEC client and device manager

## Installation

```bash
pip install pylsp-bec
```

## What it provides

- Autocompletion for `bec`, `dev`, `scans` objects
- Support for movement functions (`mv`, `mvr`, `umv`, `umvr`)
- Integration with numpy as `np`
- Real-time device and scan method signatures

Requires `python-lsp-server` and `bec_lib` to function.
