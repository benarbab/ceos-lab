# ⚙️ Kernel Installation

---

1. Download the Kernel Folder into your Ubuntu VM
2. Run the following commands in your Ubuntu:
   
```bash
sudo cp ~/kernel/vmlinuz-5.4.164 /boot/
sudo cp ~/kernel/initrd.img-5.4.164 /boot/
sudo cp ~/kernel/System.map-5.4.164 /boot/
sudo cp ~/kernel/config-5.4.164 /boot/
sudo tar -xzf ~/kernel/modules-5.4.164.tar.gz -C /lib/modules/
```

3. Update the Grub

```bash
sudo update-grub
```

4. Open the Grub

```bash
sudo nano /etc/default/grub
```

5. Edit the file and save

```text
Comment out this line:
GRUB_DEFAULT=0

And add this:
GRUB_DEFAULT="Advanced options for Ubuntu>Ubuntu, with Linux 5.4.164"
```

6. Update the Grub

```bash
sudo update-grub
```

7. Reboot

```bash
sudo reboot
```

8. Check the Kernel version

```bash
uname -r

output
5.4.164
```
