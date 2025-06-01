import os
from main_functions import vm_del, net_del
from proxmoxer import ProxmoxAPI
from settings import *


# Подключение API
if USE_PASSWORD:
    proxmox = ProxmoxAPI(SERVER, user=USER, password=PASSWORD, verify_ssl=False, service='PVE')
else:
    proxmox = ProxmoxAPI(SERVER, user=USER, token_name=API_TOKEN_ID, token_value=API_TOKEN, verify_ssl=False, service='PVE')

# Удаление виртуальных машин
vm_del(proxmox)

# Удаление виртуальных сетей
net_del(proxmox)

# Удаление пользователя и пула
if 'module-1' in [pool['poolid'] for pool in proxmox.pools.get()]:
    proxmox.pools('module-1').delete()
    print("Pool module-1 - removed")
if 'module-1@pve' in [user['userid'] for user in proxmox.access.users.get()]:
    proxmox.access.users('module-1@pve').delete()
    print("User module-1@pve - removed")
if os.path.exists(f'logs/{SERVER}-{NODE}.json'):
    os.remove(f'logs/{SERVER}-{NODE}.json')
    print(f"{SERVER}-{NODE}.json - removed")
