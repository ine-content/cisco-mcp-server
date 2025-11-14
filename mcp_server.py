#!/usr/bin/env python3
"""
Cisco MCP Server (Minimal / Cisco-Standard)

Implements ONLY the tools required by official Cisco MCP behavior:
  - list_devices
  - run_command  (any show/exec command)
  - run_config   (any config commands)

Everything else (get_version, get_interfaces, set ip, etc.)
is handled by the LLM using these universal primitives.
"""

import argparse
import yaml
from fastmcp import FastMCP
from netmiko import ConnectHandler

mcp = FastMCP("Cisco-MCP-Minimal")

DEVICES = {}

# ------------------------------
# Inventory Loader
# ------------------------------
def load_inventory(path: str):
    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}
    devices = data.get("devices", {})
    if not devices:
        raise ValueError("Inventory must contain 'devices:'")
    return devices

def get_conn(device):
    d = DEVICES[device]
    conn = ConnectHandler(
        device_type=d.get("device_type", "cisco_ios"),
        host=d["host"],
        username=d["username"],
        password=d["password"],
        port=int(d.get("port", 22)),
        fast_cli=True
    )
    return conn

# ------------------------------
# MCP Tools (Cisco-standard)
# ------------------------------
@mcp.tool
def list_devices():
    """Return available device names."""
    return {"devices": list(DEVICES.keys())}

@mcp.tool
def run_command(command: str, device: str):
    """Run any show/exec command."""
    conn = get_conn(device)
    out = conn.send_command(command)
    conn.disconnect()
    return {"device": device, "command": command, "output": out}

@mcp.tool
def run_config(commands: list[str], device: str, save: bool = False):
    """Run any config commands."""
    conn = get_conn(device)
    out = conn.send_config_set(commands)
    if save:
        out += "\n" + conn.send_command("write memory")
    conn.disconnect()
    return {"device": device, "commands": commands, "output": out, "saved": save}

# ------------------------------
# Main
# ------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", default="devices.yaml")
    args = parser.parse_args()

    DEVICES = load_inventory(args.inventory)
    mcp.run(transport="stdio")

