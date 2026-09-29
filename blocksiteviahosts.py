import os

sites=["facebook.com","youtube.com"]
hosts="C:\\windows\\\system32\\drivers\\etc\\hosts"

for site in sites:
    open(hosts,"a").write(f"\n172.0.0.1 {site}")
    print(f"Blocked {site}")
