import platform
import socket
import psutil
import datetime
import getpass
import os

# Gather system information
system_info = {
    "Report Generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "Hostname": socket.gethostname(),
    "Username": getpass.getuser(),
    "Operating System": f"{platform.system()} {platform.release()}  (Version: {platform.version()})",    
    "Architecture": f"{platform.machine()}",
    "Processor": f"{platform.processor()}",    
    "CPU Cores": f"(Physical) {psutil.cpu_count(logical=False)} (Logical) {psutil.cpu_count(logical=True)}",
    "Total Memory (GB)": round(psutil.virtual_memory().total / (1024**3), 2),
    "Available Memory (GB)": round(psutil.virtual_memory().available / (1024**3), 2),
    "IP Address": socket.gethostbyname(socket.gethostname()),
    "Boot Time": datetime.datetime.fromtimestamp(
        psutil.boot_time()
    ).strftime("%Y-%m-%d %H:%M:%S"),
}

# Disk information
disk_rows = []
for partition in psutil.disk_partitions():
    try:
        usage = psutil.disk_usage(partition.mountpoint)
        disk_rows.append(
            f"""
            <tr>
                <td>{partition.device}</td>
                <td>{partition.mountpoint}</td>
                <td>{round(usage.total / (1024**3), 2)} GB</td>
                <td>{round(usage.used / (1024**3), 2)} GB</td>
                <td>{round(usage.free / (1024**3), 2)} GB</td>
                <td>{usage.percent}%</td>
            </tr>
            """
        )
    except Exception:
        pass

# HTML report
html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>System Information Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        h1 {{
            color: #0078D4;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #0078D4;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
    </style>
</head>
<body>

<h1>System Information Report</h1>

<table>
    <tr><th>Property</th><th>Value</th></tr>
"""

for key, value in system_info.items():
    html += f"<tr><td>{key}</td><td>{value}</td></tr>"

html += f"""
</table>

<h2>Disk Information</h2>
<table>
    <tr>
        <th>Device</th>
        <th>Mount Point</th>
        <th>Total</th>
        <th>Used</th>
        <th>Free</th>
        <th>Usage %</th>
    </tr>
    {''.join(disk_rows)}
</table>

</body>
</html>
"""

# Save report
output_file = "system_report.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Report generated: {os.path.abspath(output_file)}")
