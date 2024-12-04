from os import path as ospath
import subprocess
import shutil

class USBDevice():
    def __init__(self, img_path, mount_point, image_size=2048):
        if not ospath.exists(img_path):
            subprocess.run(['dd', 'if=/dev/zero', f'of={img_path}', 'bs=1M', f'count={image_size}']).check_returncode()
            subprocess.run(['mkfs.fat', '-F', '32', img_path]).check_returncode()
        self.img_path = img_path
        subprocess.run(['mkdir', '-p', mount_point]).check_returncode()
        self.mount_point = mount_point
        self.image_size = image_size
        self.is_connected = False

    def _is_mounted_locally(self):
        with open('/proc/mounts', 'r') as f:
            mounts = f.read()
            if self.mount_point in mounts:
                return True

        return False
    
    def teardown(self):
        if self._is_mounted_locally():
            self.unmount_local()

        if self.is_connected:
            self.disable_usb()

        subprocess.run(['rm', '-rf', self.mount_point]).check_returncode()
        subprocess.run(['rm', self.img_path]).check_returncode()


    def mount_local(self):
        if self._is_mounted_locally():
            return
        subprocess.run(['mount', '-o', 'loop', self.img_path, self.mount_point]).check_returncode()
    
    def unmount_local(self):
        if self._is_mounted_locally():
            subprocess.run(['umount', self.mount_point]).check_returncode()

    def add_file(self, file_path, dst_path):
        if self.is_connected:
            self.disable_usb()
        self.mount_local()
        shutil.copy(file_path, ospath.join(self.mount_point, dst_path))
        self.unmount_local()

    def enable_usb(self):
        if self._is_mounted_locally():
            self.unmount_local()
        subprocess.run(['modprobe', 'g_mass_storage', 'file=' + ospath.abspath(self.img_path), 'removable=1', 'ro=0', 'stall=0']).check_returncode()
        
        self.is_connected = True

    def disable_usb(self):
        subprocess.run(['modprobe', '-r', 'g_mass_storage']).check_returncode()
        self.is_connected = False
