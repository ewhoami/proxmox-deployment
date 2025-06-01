from proxmoxer import ProxmoxAPI
import os
from main_functions import (base_check, ipf_check, iptables_check,
                            gre_check, na_check, frr_check, dnsmasq_check, ssh_check,
                            iface_mode_check, nslookup)
from settings import SERVER, USER, PASSWORD, API_TOKEN_ID, API_TOKEN, NODE, USE_PASSWORD

# Подключение API
if USE_PASSWORD:
    proxmox = ProxmoxAPI(SERVER, user=USER, password=PASSWORD, verify_ssl=False, service='PVE')
else:
    proxmox = ProxmoxAPI(SERVER, user=USER, token_name=API_TOKEN_ID, token_value=API_TOKEN, verify_ssl=False, service='PVE')

# Открытие файла
os.makedirs("results", exist_ok=True)
file = open(f'results/{SERVER}-{NODE}.txt', 'w')

# Список vmid
vmids = {
        'ISP': 100,
        'HQ-RTR': 101,
        'BR-RTR': 102,
        'HQ-SRV': 103,
        'BR-SRV': 104,
        'HQ-CLI': 105,
    }

# Доменные имена (для nslookup)
domain_names = ['hq-rtr.au-team.irpo', 'br-rtr.au-team.irpo',
                'hq-srv.au-team.irpo', 'br-srv.au-team.irpo',
                'hq-cli.au-team.irpo', 'moodle.au-team.irpo',
                'wiki.au-team.irpo']

# ISP
print("Collecting data from ISP...")
base_check(proxmox, 'ISP', vmids['ISP'], file)
ipf_check(proxmox, vmids['ISP'], file)
iptables_check(proxmox, vmids['ISP'], file)

# HQ-RTR
print("Collecting data from HQ-RTR...")
base_check(proxmox, 'HQ-RTR', vmids['HQ-RTR'], file)
gre_check(proxmox, vmids['HQ-RTR'], file)
ipf_check(proxmox, vmids['HQ-RTR'], file)
na_check(proxmox, vmids['HQ-RTR'], file)
iptables_check(proxmox, vmids['HQ-RTR'], file)
frr_check(proxmox, vmids['HQ-RTR'], file)
dnsmasq_check(proxmox, vmids['HQ-RTR'], file)
file.write("\n")

# BR-RTR
print("Collecting data from BR-RTR...")
base_check(proxmox, 'BR-RTR', vmids['BR-RTR'], file)
gre_check(proxmox, vmids['BR-RTR'], file)
ipf_check(proxmox, vmids['BR-RTR'], file)
na_check(proxmox, vmids['BR-RTR'], file)
iptables_check(proxmox, vmids['BR-RTR'], file)
frr_check(proxmox, vmids['BR-RTR'], file)
file.write("\n")

# HQ-SRV
print("Collecting data from HQ-SRV...")
base_check(proxmox, 'HQ-SRV', vmids['HQ-SRV'], file)
ssh_check(proxmox, vmids['HQ-SRV'], file)
file.write("\n")

# BR-SRV
print("Collecting data from BR-SRV...")
base_check(proxmox, 'BR-SRV', vmids['BR-SRV'], file)
ssh_check(proxmox, vmids['BR-SRV'], file)
nslookup(proxmox, vmids['BR-SRV'], domain_names, file)
file.write("\n")

# HQ-CLI
print("Collecting data from HQ-CLI...")
base_check(proxmox, 'HQ-CLI', vmids['HQ-CLI'], file)
iface_mode_check(proxmox, vmids['HQ-CLI'], file)
nslookup(proxmox, vmids['HQ-CLI'], domain_names, file)

file.close()
print(f"\nResult file {SERVER}-{NODE}.txt is located in the results directory")
