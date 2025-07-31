#!/bin/bash

set -e

# Step 1: Enable and start haveged
echo "🚀 Enabling and starting haveged..."
sudo systemctl enable --now haveged

# Step 2: Final verification
echo "✅ ===== HAVEGED STATUS ====="
systemctl status haveged --no-pager

echo "📈 ===== FINAL ENTROPY ====="
cat /proc/sys/kernel/random/entropy_avail

