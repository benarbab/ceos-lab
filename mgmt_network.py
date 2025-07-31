#!/usr/bin/env python3

import subprocess
import yaml
import os


def is_podman():
    try:
        out = subprocess.check_output(["docker", "--version"], stderr=subprocess.STDOUT).decode()
        return "podman" in out.lower()
    except Exception:
        return False


def list_physical_interfaces():
    return [
        iface for iface in os.listdir('/sys/class/net')
        if iface != 'lo' and not iface.startswith('docker') and not iface.startswith('br-')
    ]


def create_macvlan_network(dry_run=False, parent=None):
    name = 'a-135'
    subnet = '192.168.150.0/24'
    gateway = '192.168.150.1'

    if not parent:
        interfaces = list_physical_interfaces()
        if not interfaces:
            raise RuntimeError("❌ No usable interfaces found. Please specify one with --parent.")
        parent = interfaces[0]

    print(f"\n⚙️  Creating a new macvlan network:")
    print(f"   Name: {name}")
    print(f"   Subnet: {subnet}")
    print(f"   Gateway: {gateway}")
    print(f"   Parent interface: {parent}")
    mode = input("👉 Choose mode [bridge/private/vepa/passthru] (default: bridge): ").strip().lower()
    if mode not in ('bridge', 'private', 'vepa', 'passthru'):
        mode = 'bridge'

    if dry_run:
        print(f"📝 Dry-run: would create macvlan network '{name}' on '{parent}' with {subnet}, gateway {gateway}, mode {mode}")
        return name, mode, True

    if is_podman():
        args = [
            "podman", "network", "create",
            "--driver", "macvlan",
            "--subnet", subnet,
            "--gateway", gateway,
            "--interface", parent,
            "--mode", mode,
            name
        ]
    else:
        args = [
            "docker", "network", "create", "-d", "macvlan",
            "--subnet", subnet, "--gateway", gateway,
            "-o", f"parent={parent}",
            "-o", f"macvlan_mode={mode}",
            name
        ]

    subprocess.run(args, check=True)
    print(f"✅ Created macvlan network '{name}' on '{parent}' in mode '{mode}'")
    return name, mode, True


def ensure_or_select_mgmt_network(topo_file, auto=False, dry_run=False, parent=None):
    while True:
        existing = list_existing_macvlan_networks()
        if existing:
            print("\n📋 Existing macvlan networks:")
            for idx, (name, iface, mode) in enumerate(existing, 1):
                print(f"  {idx}. {name} → {iface} [mode: {mode}]")
            choice = input("👉 Choose one or [C]reate new: ").strip().lower()
            if choice == 'c':
                mgmt_net, mode, created = create_macvlan_network(dry_run, parent)
            else:
                mgmt_net, _, mode = existing[int(choice)-1]
                created = False
        else:
            mgmt_net, mode, created = create_macvlan_network(dry_run, parent)

        if mode != 'private':
            print(f"⚠️ WARNING: public mode. LLDP/broadcast frames may reach your mgmt network.")
            if input("❓ Continue anyway? [y/N]: ").strip().lower() != 'y':
                continue

        break

    if dry_run:
        print(f"📝 Dry-run: would update topology.yml with management_network: {mgmt_net}")
        return mgmt_net, created

    with open(topo_file) as f:
        topo = yaml.safe_load(f)
    if topo.get('management_network') != mgmt_net:
        topo['management_network'] = mgmt_net
        with open(topo_file, 'w') as f:
            yaml.dump(topo, f, sort_keys=False)

    return mgmt_net, created


def list_existing_macvlan_networks():
    output = subprocess.check_output(
        ['docker', 'network', 'ls', '--filter', 'driver=macvlan', '--format', '{{.Name}}']
    ).decode().splitlines()

    networks = []
    for name in output:
        inspect = yaml.safe_load(subprocess.check_output(['docker', 'network', 'inspect', name]).decode())[0]
        parent = inspect.get('Options', {}).get('parent', 'unknown')
        mode = inspect.get('Options', {}).get('macvlan_mode', 'bridge')
        mode_str = 'private' if mode == 'private' else 'public'
        networks.append((name, parent, mode_str))
    return networks
