#!/bin/bash

set -e

echo "🧹 Cleaning up broken repo if exists..."
sudo rm -f /etc/yum.repos.d/almalinux.repo

# Step 1: Check entropy
ENTROPY=$(cat /proc/sys/kernel/random/entropy_avail)
echo "🔎 Current entropy: $ENTROPY"

if [ "$ENTROPY" -lt 100 ]; then
  echo "⚠️ Entropy below 100. Applying temporary boost..."
  sudo dd if=/dev/urandom of=/dev/null bs=1M count=100 status=none
fi

# Step 2: Install EPEL release
echo "📦 Installing EPEL release..."
sudo dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm

# Step 3: Clean and refresh DNF metadata
echo "🔄 Cleaning and rebuilding DNF cache..."
sudo dnf clean all
sudo dnf makecache

# Step 4: Install haveged
echo "⚙️ Installing haveged..."
sudo dnf install -y haveged

# Step 5: Enable and start haveged
echo "🚀 Enabling and starting haveged..."
sudo systemctl enable --now haveged

# Step 6: Final verification
echo "✅ ===== HAVEGED STATUS ====="
systemctl status haveged --no-pager

echo "📈 ===== FINAL ENTROPY ====="
cat /proc/sys/kernel/random/entropy_avail

