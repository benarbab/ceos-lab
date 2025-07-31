#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
RESET='\033[0m'

lldp_bit=16384

list_bridges() {
    echo -e "${YELLOW}🔷 Available bridges:${RESET}"
    for b in /sys/class/net/*/bridge; do
        br=$(basename "$(dirname "$b")")
        echo "  - $br"
    done
}

show_status() {
    local br=$1
    mask=$(cat /sys/class/net/$br/bridge/group_fwd_mask)
    if (( mask & lldp_bit )); then
        echo -e "  $br: ${GREEN}LLDP ENABLED${RESET} (group_fwd_mask=$mask)"
    else
        echo -e "  $br: ${RED}LLDP DISABLED${RESET} (group_fwd_mask=$mask)"
    fi
}

disable_lldp() {
    local br=$1
    mask=$(cat /sys/class/net/$br/bridge/group_fwd_mask)
    new_mask=$(( mask & ~lldp_bit ))
    echo $new_mask > /sys/class/net/$br/bridge/group_fwd_mask
    echo -e "${GREEN}✅ LLDP disabled on $br (group_fwd_mask=$new_mask)${RESET}"
}

enable_lldp() {
    local br=$1
    mask=$(cat /sys/class/net/$br/bridge/group_fwd_mask)
    new_mask=$(( mask | lldp_bit ))
    echo $new_mask > /sys/class/net/$br/bridge/group_fwd_mask
    echo -e "${GREEN}✅ LLDP enabled on $br (group_fwd_mask=$new_mask)${RESET}"
}

main() {
    list_bridges
    echo
    read -p "👉 Enter bridge name to manage: " br

    if [ ! -f /sys/class/net/$br/bridge/group_fwd_mask ]; then
        echo -e "${RED}❌ Bridge $br does not exist or is not a Linux bridge.${RESET}"
        exit 1
    fi

    show_status $br
    echo
    echo -e "${YELLOW}What do you want to do?${RESET}"
    echo "  1) Disable LLDP"
    echo "  2) Enable LLDP"
    echo "  q) Quit"
    read -p "👉 Your choice: " choice

    case $choice in
        1)
            disable_lldp $br
            ;;
        2)
            enable_lldp $br
            ;;
        q)
            echo "👋 Bye!"
            ;;
        *)
            echo -e "${RED}Invalid choice.${RESET}"
            ;;
    esac

    echo
    echo "📋 Current Status:"
    show_status $br
}

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run as root${RESET}"
    exit 1
fi

main

