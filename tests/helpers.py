"""Helpers that load a contract file against the offline GenVM shim."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHIM_DIR = ROOT / "tools" / "genshim"

OWNER = "0x" + "a1" * 20
AGENT = "0x" + "b2" * 20
PAYEE = "0x" + "c3" * 20
STRANGER = "0x" + "d4" * 20
ZERO_ADDRESS = "0x" + "0" * 40

GEN = 10 ** 18

_load_counter = 0


def load_contract(relative_path: str):
    """Import a contract file with `genlayer` resolving to the local shim.

    Each call gets a fresh shim instance, so mocks, message context and the
    transfer log never leak between tests.
    """
    global _load_counter
    _load_counter += 1
    module_name = f"contract_under_test_{_load_counter}"

    sys.path.insert(0, str(SHIM_DIR))
    try:
        spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(SHIM_DIR))
        sys.modules.pop("genlayer", None)


def deploy_mandate():
    module = load_contract("contracts/agent_mandate.py")
    return module, module.AgentMandate()


def transfers(module) -> list[tuple[str, int]]:
    """Every emit_transfer the contract made, in order, as (address, value)."""
    return list(module.gl.evm.sent_log)
