# 🚀 Docker Topology Generator for cEOS

This Python script generates a `docker-compose.yml` and per-device configuration files for a cEOS lab topology based on an input YAML topology file.  
It also detects existing `ceos` Docker images and allows the user to pick one interactively.

---

## 📑 Table of Contents

- [🚀 Docker Topology Generator for cEOS](#-docker-topology-generator-for-ceos)
  - [📑 Table of Contents](#-table-of-contents)
  - [Requirements](#requirements)
  - [🛑 Before you Begin](#-before-you-begin)
    - [📝 Available Options](#-available-options)
  - [📋 Features](#-features)
  - [📂 Directory Structure](#-directory-structure)
  - [🔧 Requirements](#-requirements)
    - [📡 Management Network](#-management-network)
  - [⏩ Quick Start](#-quick-start)
    - [Interactive](#interactive)
      - [1️⃣ Generate the docker-compose.yml](#1️⃣-generate-the-docker-composeyml)
      - [2️⃣ Interactive Mode](#2️⃣-interactive-mode)
    - [Manual](#manual)
      - [1️⃣ Generate the docker-compose.yml](#1️⃣-generate-the-docker-composeyml-1)
      - [2️⃣ Start the Lab and Containers](#2️⃣-start-the-lab-and-containers)
      - [3️⃣ Fix LLDP](#3️⃣-fix-lldp)
      - [4️⃣ Change MTU(Optional)](#4️⃣-change-mtuoptional)
      - [5️⃣ Connect to Containers](#5️⃣-connect-to-containers)
      - [6️⃣ Terminate the lab](#6️⃣-terminate-the-lab)
  - [📝 Usage](#-usage)
    - [Input Topology File](#input-topology-file)
    - [Command Line Options](#command-line-options)
  - [📦 Example Output](#-example-output)
  - [📄 Key Files Generated](#-key-files-generated)
    - [🔷  What is `TFA_VERSION=2`?](#--what-is-tfa_version2)
  - [🐳 Run the lab with Docker](#-run-the-lab-with-docker)
    - [🔬🧪 Name of the Lab](#-name-of-the-lab)
  - [🛑 Tear Down the Lab](#-tear-down-the-lab)
  - [🔄 Entropy and cEOS](#-entropy-and-ceos)
    - [Why does entropy matter?](#why-does-entropy-matter)
  - [🧰 Enabling Haveged in cEOS](#-enabling-haveged-in-ceos)
  - [🛑 Notes](#-notes)
  - [📚 Extending](#-extending)

---

## Requirements

- Virtual machine or Bare metal with 24G memory
- Ubuntu LTS
- Docker a and Docker Compose
- One of the cEOS container image, you can download from Arista website
- Some Linux Knowledge

---

## 🛑 Before you Begin

It’s important to run this lab on a host that already supports LLDP and LACP. You might be able to enable LLDP (using lab-helper.py), which can also adjust the MTU on bridge interfaces. However, on most Linux machines, LACP cannot be enabled simply by changing the group_fwd_mask.  

### 📝 Available Options

- Use a Linux with custom kernel to allow LLDP, LACP (Advanced)
- Use available Linux version used for iOU, EVE-NG, Container-Lab
- Download the Kernel included in this Repo - You can find it in the main folder - 📄 [Kernel Installation Instructions](KERNEL_INSTALLATION.md)

---

## 📋 Features

- Parses a YAML topology file describing devices and connections.
- Validates topology file structure & contents.
- Detects existing macvlan networks and lets you pick one.
- Or guides you through creating a new macvlan tied to a physical host interface.
- Automatically updates `topology.yml` with the chosen management network.
- Detects existing Docker networks (subnets) to avoid conflicts.
- Automatically assigns non-overlapping subnets to each link.
- Lists available `ceos` / `ceos64` Docker images and lets you choose.
- Generates:
  - `docker-compose.yml` to deploy the topology.
  - `devices/<device>/ceos-config` and `EosIntfMapping.json` for each device.
- Supports:
  - 📝 Dry-run mode (`--dry-run`)
  - 🤖 Automation-friendly mode (`--auto`)
  - 🪵 Verbose logging (`--verbose`)

---

## 📂 Directory Structure

After running the script:

```text
.
├── docker-compose.yml
├── devices/
│   ├── device1/
│   │   ├── ceos-config
│   │   └── EosIntfMapping.json
│   ├── device2/
│   │   ├── ceos-config
│   │   └── EosIntfMapping.json
│   └── ...
```

---

## 🔧 Requirements

- Python 3
- Docker installed & running
- At least one cEOS Docker image (`ceos` or `ceos64`) imported

If you don’t already have a cEOS image, you can download it from the [Arista support portal](https://www.arista.com/en/support/software-download).  
Once downloaded (typically as a `.tar.xz` file), import it into Docker using:

```bash
docker import cEOS64-lab-4.34.1F.tar.xz ceos64:4.34.1F
```

Replace the filename and tag with the version you downloaded.

---

### 📡 Management Network

⚠️ **Important:**

The script now fully manages the Docker macvlan network used for management.
If no macvlan network exists, or if you want to use a different one, the script will:

- Detect all existing macvlan networks and let you pick one.
- Or guide you through creating a new macvlan tied to a physical host interface.
- Automatically update `topology.yml` with the chosen network name.
  
You no longer need to manually create or configure the management network beforehand — the script handles it for you interactively or in `--auto` mode.  

If you still prefer to create a macvlan network manually or want to learn more, see:

📄 [Setup Management Network](SETUP_MANAGEMENT_NETWORK.md)

---

## ⏩ Quick Start

### Interactive

#### 1️⃣ Generate the docker-compose.yml  

```bash
python3 generate-lab.py topology.yml
```

#### 2️⃣ Interactive Mode  

```bash
python3 start-lab.py
```

### Manual

#### 1️⃣ Generate the docker-compose.yml  

```bash
python3 generate-lab.py topology.yml
```

#### 2️⃣ Start the Lab and Containers  

```bash
docker-compose up -d
```

#### 3️⃣ Fix LLDP  

```bash
python3 lab-helper.py -f ceos-lab_docker
```

#### 4️⃣ Change MTU(Optional)  

```bash
python3 lab-helper.py -m 9000 ceos-lab_docker
```

#### 5️⃣ Connect to Containers

```bash
python3 connect_to_lab.py
```

Or with tmux:

```bash
python3 connect_to_lab.py --method tmux
```

#### 6️⃣ Terminate the lab

```bash
docker-compose down
```

---

## 📝 Usage

### Input Topology File

```yaml
management_network: a-135
subnet_pool: 172.16.0.0/16
connections:
  - { device1: SPINE1, intf1: Ethernet1/1,  device2: LEAF1,  intf2: Ethernet1 }
  - { device1: SPINE1, intf1: Ethernet1/2,  device2: LEAF1,  intf2: Ethernet2 }
```

---

### Command Line Options

| Option          | Default        | Description                                |
|-----------------|----------------|--------------------------------------------|
| filename.yml    | `topology.yml` | Topology YAML file                        |
| `--auto`        | `False`        | Non-interactive mode                      |
| `--dry-run`     | `False`        | Validate & show actions, no changes      |
| `--verbose`     | `False`        | Detailed logging                         |
| `-h`, `--help`  |                | Show help & exit                         |

---

## 📦 Example Output

```text
✅ docker-compose.yml generated successfully. 🎉
👉 To start your lab:
   docker-compose up -d

👉 To tear it down:
   docker-compose down
```

---

## 📄 Key Files Generated

| File                                | Purpose                                 |
|------------------------------------|-----------------------------------------|
| `docker-compose.yml`              | Docker Compose file                    |
| `devices/<device>/ceos-config`    | Device config with MAC & serial        |
| `devices/<device>/EosIntfMapping.json` | Interface mappings                |

---

### 🔷  What is `TFA_VERSION=2`?

Use the newer single-file cEOS image with integrated persistent filesystem (TFA v2).  
Simplifies deployment — no need for separate `ceos-config` tarball.

---

## 🐳 Run the lab with Docker

```bash
docker-compose up -d
```

### 🔬🧪 Name of the Lab

The lab name is the folder name where `docker-compose.yml` resides.  
You’ll need it for LLDP/MTU fixes.

---

## 🛑 Tear Down the Lab

```bash
docker-compose down
```

---

## 🔄 Entropy and cEOS

### Why does entropy matter?

Low entropy can cause SSH, key generation, and boot to hang.  
Use haveged inside cEOS containers to fix.

---

## 🧰 Enabling Haveged in cEOS

```bash
docker exec -it <container> bash
cd /mnt/flash
./enable_entropy.sh
```

---

## 🛑 Notes

- Detects or creates management network as needed.
- Subnet pool defaults to `172.16.0.0/16`.

---

## 📚 Extending

Ideas:

- More validations & tests
- Parallel deployment & scaling
