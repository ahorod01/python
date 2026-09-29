"""
------------------------------------------
Filename....: SystemInfo.py
Author......: Alex Horodenski
Created.....: 2026-08-25
Last Updated: 2026-08-25
------------------------------------------
"""
import sys
import subprocess

def is_module_installed(module_name):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def install_module(module_name):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', module_name], stdout=subprocess.DEVNULL)

# Example usage
#pip install psutil
#pip install pyttsx3
#pip install ifaddr
#pip install python-nmap
package_name = 'psutil'
if not is_module_installed(package_name):
    install_module(package_name)
package_name = 'pyttsx3'
if not is_module_installed(package_name):
    install_module(package_name)
package_name = 'ifaddr'
if not is_module_installed(package_name):
    install_module(package_name)
package_name = 'python-nmap'
if not is_module_installed(package_name):
    install_module(package_name)     
    

import platform
import shutil
import os
#import pyttsx3
import psutil
import ifaddr
import socket
import winreg
import time

from datetime import datetime

#---------------------------------------------------------------------
#GENERAL FUNCTIONS DEFINITIONS HERE
#---------------------------------------------------------------------
#os.system('cls' if os.name == 'nt' else 'clear')
def clear_screen():
    """
    Clears the terminal screen on Windows, Linux, and macOS.
    """
    try:
        # Detect the operating system
        current_os = platform.system()
        
        if current_os == "Windows":
            os.system('cls')    # Windows clear command
        else:
            os.system('clear')  # Unix/Linux/Mac clear command
    except Exception as e:
        print(f"Error clearing screen: {e}")
#---------------------------------------------------------------------
def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor
#---------------------------------------------------------------------
def get_memory_info():
    """
    Retrieves and prints system memory usage details.
    Works on Windows, macOS, and Linux.
    """
    try:
        mem = psutil.virtual_memory()

        total_gb = mem.total / (1024 ** 3)
        available_gb = mem.available / (1024 ** 3)
        used_gb = mem.used / (1024 ** 3)
        percent_used = mem.percent

        print(f"Total Memory     : {total_gb:.2f} GB")
        print(f"Available Memory : {available_gb:.2f} GB")
        print(f"Used Memory      : {used_gb:.2f} GB")
        print(f"Usage Percentage : {percent_used:.2f}%")

    except Exception as e:
        print(f"Error retrieving memory info: {e}")
#---------------------------------------------------------------------
def get_local_ip():
    try:
        # Create a socket connection
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return str(e)
#---------------------------------------------------------------------
def get_installed_software_registry():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        for i in range(winreg.QueryInfoKey(key)[0]):
            subkey_name = winreg.EnumKey(key, i)
            subkey = winreg.OpenKey(key, subkey_name)
            try:
                name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                print(name)
            except Exception as e:
                print(f"Error reading {subkey_name}: {e}")
    except Exception as e:
        print(f"Error opening registry key: {e}")
#---------------------------------------------------------------------        
def get_serial_number():
    os_type = sys.platform.lower()

    if "win" in os_type: # Windows
        command = "wmic bios get serialnumber"
    elif "linux" in os_type: # Linux
        command = "dmidecode -s system-serial-number"
    elif "darwin" in os_type: # macOS
        command = "ioreg -l | grep IOPlatformSerialNumber"
    else:
        return "Unsupported OS"

    try:
        result = os.popen(command).read().strip()
        return result
    except Exception as e:
        return f"Error: {e}"
#---------------------------------------------------------------------        
def timestamp_to_iso(timestamp):
    return datetime.fromtimestamp(timestamp).astimezone().isoformat(timespec="seconds")
#---------------------------------------------------------------------
def seconds_to_human(seconds):
    if seconds is None or seconds < 0:
        return "N/A"
    seconds = int(seconds)
    days, remainder = divmod(seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)
#---------------------------------------------------------------------
"""
BEGIN HERE
"""
clear_screen()

#engine = pyttsx3.init()
#text   = "Here is your system information"
#engine.say(text)
#engine.runAndWait()

#print("Hostname: " + platform.node())
hostname = socket.gethostname()
IPAddr   = socket.gethostbyname(hostname)           
print("Your Computer Name is......:", hostname)
print("Your Computer IP Address is:", IPAddr)
print(f"Architecure................: {platform.machine()}")
print(f"Processor..................: {platform.processor()}")
print(f"Physical cores: {psutil.cpu_count(logical=False)}")
print(f"Total cores: {psutil.cpu_count(logical=True)}")
cpufreq = psutil.cpu_freq()
print(f"Max Frequency: {cpufreq.max:.2f}Mhz")
print(f"Current Frequency: {cpufreq.current:.2f}Mhz")
print("CPU Usage Per Core:")
for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
    print(f"Core {i}: {percentage}%")
print(f"Total CPU Usage: {psutil.cpu_percent()}%")
print("Serial Number:", get_serial_number())

print("="*10, "Boot Time", "="*10)
#method 1
boot_time = datetime.fromtimestamp(psutil.boot_time())
print(f"Boot Time: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}")
#method 2
uname = platform.uname()
boot_time = psutil.boot_time()
print("Boot time:", timestamp_to_iso(boot_time))
print("Uptime:", seconds_to_human(time.time() - boot_time))


print("=======================")
print("Storage (aka Diskspace)")
print("=======================")
# Path can be a directory or file (on Unix), must be a directory on Windows
path = "/"
total, used, free = shutil.disk_usage(path)
print(f"Total: {total // (2**30)} GB")
print(f"Used.: {used // (2**30)} GB")
print(f"Free.: {free // (2**30)} GB")

print("=======================")
print("Memory")
print("=======================")
#method 1
if __name__ == "__main__":
    get_memory_info()
#method 2    
svmem = psutil.virtual_memory()
print(f"Total.....: {get_size(svmem.total)}")
print(f"Available.: {get_size(svmem.available)}")
print(f"Used......: {get_size(svmem.used)}")
print(f"Percentage: {svmem.percent}%")


print("=======================")
print("Network Interfaces")
print("=======================")
# Get a dictionary of network interfaces
#interfaces = psutil.net_if_addrs()
# Print the names of all network interfaces
#print(list(interfaces.keys()))
adapters = ifaddr.get_adapters()
for adapter in adapters:
    print(adapter.nice_name)
print("Local IP:", get_local_ip())

print("=======================")
print("OS Platform and Version")
print("=======================")
uname = platform.uname()
print(f"{platform.system()} {platform.release()} ({uname.version})")

print("=======================")
print("\n**INSTALLED SOFTWARE**")
print("=======================")
get_installed_software_registry()





