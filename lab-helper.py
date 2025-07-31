import subprocess
import re
import sys
import argparse

def fix_lldp(bridge_ids):
    # Iterate through the list of bridge_ids and enable LLDP for each one
    for bridge_id in bridge_ids:
        print(f"Enabling LLDP on br-{bridge_id}")
        command = f"echo 16384 > /sys/class/net/br-{bridge_id}/bridge/group_fwd_mask"
        subprocess.run(command, shell=True, check=True)

def mtu(bridge_id, mtu_size):
    # Run the brctl command to get the list of interfaces in the specified bridge
    command = f"brctl show br-{bridge_id}"
    try:
        result = subprocess.check_output(command, shell=True, universal_newlines=True)
        lines = result.strip().split('\n')

        # Iterate through the lines and extract interface names starting with "ve"
        for line in lines:
            match = re.findall(r've\w+', line)
            if match:
                for interface in match:
                    print(f"MTU change to {mtu_size} on {interface}")
                    # Use the ip command to set the MTU size for the interface
                    subprocess.run(["ip", "link", "set", "dev", interface, "mtu", str(mtu_size)])
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

def main(lab_name, run_fix_lldp=False, mtu_size=None):
    # Run the "docker network ls" command and capture its output
    output = subprocess.check_output(["docker", "network", "ls"], universal_newlines=True)

    # Use regular expression to find items starting with the provided name but not ending with "_default"
    pattern = r'{}_(?!default\b)\S+'.format(lab_name)
    lab_items = re.findall(pattern, output)

    # Split the output into lines
    lines = output.splitlines()

    # Initialize a list to store all found bridge_ids
    found_bridge_ids = []

    # Find the bridge_id on the same line as each match
    for line in lines:
        for device in lab_items:
            if device in line:
                # Split the line by whitespace and store the bridge_id
                parts = line.split()
                if len(parts) > 0:
                    bridge_id = parts[0]
                    found_bridge_ids.append(bridge_id)
                    print(f"docker container: {device} with bridge_id: br-{bridge_id}")

    # Run the mtu function for each found bridge_id with the specified MTU size
    if mtu_size is not None:
        for bridge_id in found_bridge_ids:
            mtu(bridge_id, mtu_size)

    # Run the fix_lldp function for all found bridge_ids if requested
    if run_fix_lldp and found_bridge_ids:
        fix_lldp(found_bridge_ids)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage network settings for a lab")
    parser.add_argument("lab_name", help="Name of the lab - Get the lab name from Portainer's Stacks page")
    parser.add_argument("-f", "--fix-lldp", action="store_true", help="Enable LLDP")
    parser.add_argument("-m", "--mtu", type=int, help="Change MTU size (1-65535)")

    args = parser.parse_args()

    if args.mtu is not None and not (1 <= args.mtu <= 65535):
        print("Invalid MTU size. Please provide a valid MTU size between 1 and 65535.")
        sys.exit(1)

    main(args.lab_name, args.fix_lldp, args.mtu)

