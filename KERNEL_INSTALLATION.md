# ⚙️ Kernel Installation

---

1. Download the Kernel Folder into your Ubuntu VM
2. Run the following commands:
   
```bash
sudo cp ~/kernel/vmlinuz-5.4.164 /boot/
sudo cp ~/kernel/initrd.img-5.4.164 /boot/
sudo cp ~/kernel/System.map-5.4.164 /boot/
sudo cp ~/kernel/config-5.4.164 /boot/
sudo tar -xzf ~/kernel/modules-5.4.164.tar.gz -C /lib/modules/
```