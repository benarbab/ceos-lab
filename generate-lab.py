#!/usr/bin/env python3

import argparse
import os
import sys
import yaml
import ipaddress
import hashlib
import subprocess
import json
import logging
from collections import defaultdict
from mgmt_network import ensure_or_select_mgmt_network


DEFAULT_SUBNET_POOL = ipaddress.ip_network('172.16.0.0/16')


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate docker-compose.yml and device configs for cEOS lab."
    )
    parser.add_argument(
        'topology',
        nargs='?',
        default='topology.yml',
        help='Topology YAML file (default: topology.yml)'
    )
    parser.add_argument('--auto', action='store_true', help='Run in non-interactive mode with defaults')
    parser.add_argument('--dry-run', action='store_true', help='Validate everything but don’t create files or networks')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging to generate-lab.log')
    parser.add_argument('--parent', help='Specify parent interface explicitly (e.g., eth0)')
    return parser.parse_args()


def setup_logging(verbose):
    if verbose:
        logging.basicConfig(
            filename='generate-lab.log',
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s'
        )
        logging.info("Logging started")


def validate_topology(topo):
    if not isinstance(topo, dict):
        raise ValueError("Topology file is not a YAML dictionary")
    if 'connections' not in topo or not isinstance(topo['connections'], list):
        raise ValueError("Missing or invalid 'connections' section")
    for conn in topo['connections']:
        if not all(k in conn for k in ('device1', 'intf1', 'device2', 'intf2')):
            raise ValueError(f"Invalid connection entry: {conn}")


def get_existing_docker_subnets():
    output = subprocess.check_output(['docker', 'network', 'ls', '-q']).decode().splitlines()
    existing_subnets = set()
    for net_id in output:
        info = json.loads(subprocess.check_output(['docker', 'network', 'inspect', net_id]).decode())[0]
        ipam = info.get('IPAM')
        if not ipam or not ipam.get('Config'):
            continue
        for cfg in ipam['Config']:
            if 'Subnet' in cfg:
                existing_subnets.add(ipaddress.ip_network(cfg['Subnet']))
    return existing_subnets


def next_subnet(used_subnets, existing_docker_subnets, base_subnet, prefixlen=24):
    for subnet in base_subnet.subnets(new_prefix=prefixlen):
        if subnet in used_subnets or any(subnet.overlaps(existing) for existing in existing_docker_subnets):
            continue
        used_subnets.add(subnet)
        return subnet
    raise Exception("No more available subnets!")


def mac_from_name(name):
    h = hashlib.md5(name.encode()).hexdigest()
    return f'02:{h[0:2]}:{h[2:4]}:{h[4:6]}:{h[6:8]}:{h[8:10]}'


def generate_device_files(devices, connections, dry_run):
    volume_paths = {}
    interface_mapping_per_device = defaultdict(list)

    for conn in connections:
        for dev_key, intf_key in [('device1', 'intf1'), ('device2', 'intf2')]:
            interface_mapping_per_device[conn[dev_key]].append(conn[intf_key])

    if dry_run:
        print("📝 Dry-run: would generate device configs.")
        return {}

    os.makedirs('devices', exist_ok=True)

    for device, intfs in interface_mapping_per_device.items():
        device_dir = os.path.join('devices', device)
        os.makedirs(device_dir, exist_ok=True)

        with open(os.path.join(device_dir, 'ceos-config'), 'w') as f:
            f.write(f"SERIALNUMBER={device.upper()}-SN\n")
            f.write(f"SYSTEMMACADDR={mac_from_name(device)}\n")
            f.write("TFA_VERSION=2\n")

        mapping = {
            "ManagementIntf": {"eth0": "Management1"},
            "EthernetIntf": {f"eth{i+1}": iface for i, iface in enumerate(intfs)}
        }

        with open(os.path.join(device_dir, 'EosIntfMapping.json'), 'w') as f:
            json.dump(mapping, f, indent=2)

        volume_paths[device] = {
            'ceos_config': os.path.abspath(os.path.join(device_dir, 'ceos-config')),
            'eos_mapping': os.path.abspath(os.path.join(device_dir, 'EosIntfMapping.json'))
        }

    return volume_paths


def select_ceos_image(auto, dry_run):
    output = subprocess.check_output(['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}']).decode()
    images = [line for line in output.splitlines() if line.startswith('ceos')]
    if not images:
        print("❌ No ceos images found. Please import one and try again.")
        sys.exit(1)

    print("\n📋 Available ceos images:")
    for idx, img in enumerate(images, 1):
        print(f"  {idx}. {img}")

    if auto or dry_run:
        print(f"✅ Auto/Dry-run: would select {images[0]}")
        return images[0]

    while True:
        choice = input("👉 Enter the number of the image you want to use: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(images):
            return images[int(choice)-1]
        print("⚠️ Invalid choice. Try again.")


def generate_compose(devices, links, mgmt_net, volume_paths, ceos_image, dry_run):
    if dry_run:
        print("📝 Dry-run: would generate docker-compose.yml.")
        return

    compose = {'version': '3.7', 'services': {}, 'networks': {mgmt_net: {'external': True}}}

    for idx, link in enumerate(links, 1):
        net_name = f'link{idx:02d}'
        link['net_name'] = net_name
        compose['networks'][net_name] = {
            'driver': 'bridge',
            'ipam': {'config': [{'subnet': str(link["subnet"])}]}
        }

    for device in devices:
        nets = [mgmt_net] + [link['net_name'] for link in links if device in (link['device1'], link['device2'])]
        paths = volume_paths.get(device, {})

        compose['services'][device] = {
            'image': ceos_image,
            'privileged': True,
            'hostname': device,
            'volumes': [
                {'type': 'bind', 'source': paths.get("ceos_config", ""), 'target': '/mnt/flash/ceos-config', 'read_only': True},
                {'type': 'bind', 'source': paths.get("eos_mapping", ""), 'target': '/mnt/flash/EosIntfMapping.json', 'read_only': True},
                {'type': 'bind', 'source': os.path.abspath("setup_entropy.sh"), 'target': '/mnt/flash/setup_entropy.sh', 'read_only': True},
                {'type': 'bind', 'source': os.path.abspath("enable_entropy.sh"), 'target': '/mnt/flash/enable_entropy.sh', 'read_only': True},
            ],
            'environment': {
                'CEOS': '1', 'EOS_PLATFORM': 'ceoslab', 'container': 'docker',
                'ETBA': '1', 'INTFTYPE': 'eth', 'SKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT': '1'
            },
            'command': (
                '/sbin/init systemd.setenv=INTFTYPE=eth systemd.setenv=ETBA=1 '
                'systemd.setenv=CEOS=1 systemd.setenv=EOS_PLATFORM=ceoslab '
                'systemd.setenv=container=docker systemd.setenv=MAPETH0=1 '
                'systemd.setenv=MGMT_INTF=eth0'
            ),
            'networks': nets
        }

    with open('docker-compose.yml', 'w') as f:
        yaml.dump(compose, f, default_flow_style=False, sort_keys=False)


def main():
    args = parse_args()
    setup_logging(args.verbose)

    if not os.path.isfile(args.topology):
        print(f"❌ Topology file '{args.topology}' does not exist.")
        sys.exit(1)

    with open(args.topology) as f:
        topo = yaml.safe_load(f)

    try:
        validate_topology(topo)
    except Exception as e:
        print(f"❌ Invalid topology file: {e}")
        sys.exit(1)

    base_subnet = ipaddress.ip_network(topo.get('subnet_pool', str(DEFAULT_SUBNET_POOL)))
    connections = topo['connections']

    mgmt_net, _ = ensure_or_select_mgmt_network(args.topology, auto=args.auto, dry_run=args.dry_run, parent=args.parent)

    existing_docker_subnets = get_existing_docker_subnets()
    devices = {}
    used_subnets = set()
    links = []

    for link in connections:
        subnet = next_subnet(used_subnets, existing_docker_subnets, base_subnet)
        links.append({
            'device1': link['device1'], 'intf1': link['intf1'],
            'device2': link['device2'], 'intf2': link['intf2'],
            'subnet': subnet
        })
        devices.setdefault(link['device1'], set()).add(link['intf1'])
        devices.setdefault(link['device2'], set()).add(link['intf2'])

    ceos_image = select_ceos_image(auto=args.auto, dry_run=args.dry_run)
    volume_paths = generate_device_files(devices, connections, dry_run=args.dry_run)
    generate_compose(devices, links, mgmt_net, volume_paths, ceos_image, dry_run=args.dry_run)

    if not args.dry_run:
        print("\n✅ docker-compose.yml generated successfully. 🎉\n")
        print("👉 To start your lab:\n   docker-compose up -d\n\n👉 To tear it down:\n   docker-compose down\n")
        show = input("👀 Would you like to see the contents of docker-compose.yml? [y/N]: ").strip().lower()
        if show == 'y':
            with open('docker-compose.yml') as f:
                print("\n" + f.read())
    else:
        print("\n📝 Dry-run completed successfully.")


if __name__ == "__main__":
    main()
