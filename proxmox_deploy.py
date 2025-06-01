from proxmoxer import ProxmoxAPI
import subprocess, platform, sys
from settings import *
from main_functions import (vm_create, net_create, clone_vm, send_command, reconf_vm, snap, create_user,
                            create_pool, start_vm, stop_vm)
from step_manager import run_step

# Подключение API
if USE_PASSWORD:
    proxmox = ProxmoxAPI(SERVER, user=USER, password=PASSWORD, verify_ssl=False, service='PVE')
else:
    proxmox = ProxmoxAPI(SERVER, user=USER, token_name=API_TOKEN_ID, token_value=API_TOKEN, verify_ssl=False,
                         service='PVE')

# Список vmid
vmids = {
    'ISP': 100,
    'HQ-RTR': 101,
    'BR-RTR': 102,
    'HQ-SRV': 103,
    'BR-SRV': 104,
    'HQ-CLI': 105,
}

# Проверка наличия образа на сервере
if f"{ISO_STORAGE}:iso/{ISO_NAME}" not in [i['volid'] for i in proxmox.nodes(NODE).storage(ISO_STORAGE).content.get()]:
    print("The specified image is not found on the server")
    sys.exit()

# Создание виртуальных сетей
run_step("create_net_HQ_SW", net_create, proxmox, 'HQ_SW', vlan=True)
run_step("create_net_ISP_HQ", net_create, proxmox, 'ISP_HQ')
run_step("create_net_ISP_BR", net_create, proxmox, 'ISP_BR')
run_step("create_net_BR_SW", net_create, proxmox, 'BR_SW')
proxmox.nodes(NODE).networtk.put()

# Создание VM ISP
run_step("create_vm_ISP", vm_create, proxmox, vmids['ISP'], 'ISP', 1, 1024,
          f'{VM_STORAGE}:10,format=qcow2', f'{ISO_STORAGE}:iso/{ISO_NAME}',
          f'model=virtio,bridge={ISP_INTERFACE},firewall=1')
run_step("start_ISP_1", start_vm, proxmox, vmids['ISP'])

# Установка ОС
try:
    proxmox.nodes(NODE).qemu(vmids['ISP']).agent("ping").create()
except Exception:
    if USE_TEMP_HTTP:
        # Запуск временного HTTP сервера
        print("Starting temporary HTTP server...")
        python_command = "python" if platform.system() == "Windows" else "python3"
        tmphttp = subprocess.Popen([python_command, "temp_http.py"], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        print(f"Select on VM {vmids['ISP']} \"Advanced options\" > \"Automated install\" and enter "
              f"\"http://<your_ip>:{TEMP_HTTP_SRV_PORT}/preseed.cfg\"")

    # Ожидание установки ОС и остановка временного HTTP сервера
    try:
        while True:
            try:
                proxmox.nodes(NODE).qemu(vmids['ISP']).agent("ping").create()
                print("OS installed!")
                break
            except Exception:
                print(f"\rWaiting for OS installation...", end='')
    finally:
        if USE_TEMP_HTTP:
            print("Stopping temporary HTTP server...")
            tmphttp.terminate()
            tmphttp.wait()

# Установка и обновление пакетов
run_step("ISP_update", send_command, proxmox, vmids['ISP'], ['apt', 'update', '-y'])
run_step("ISP_install_sudo", send_command, proxmox, vmids['ISP'], ["apt", "install", "sudo", "-y"])
run_step("ISP_install_iptables", send_command, proxmox, vmids['ISP'], ["apt", "install", "iptables", "-y"])
run_step("ISP_install_iptables", send_command, proxmox, vmids['ISP'], ["apt", "install", "ssh", "-y"])
run_step("ISP_install_ssh", send_command, proxmox, vmids['ISP'], ["apt", "install", "ssh", "-y"])
run_step("ISP_install_ssh", send_command, proxmox, vmids['ISP'], ["apt", "disable", "ssh", "-y"])

# Создание остальных машин (клонированием)
run_step("create_HQ-RTR", clone_vm, proxmox, vmids['ISP'], vmids['HQ-RTR'], 'HQ-RTR')
run_step("start_HQ-RTR_1", start_vm, proxmox, vmids['HQ-RTR'])
run_step("create_BR-RTR", clone_vm, proxmox, vmids['ISP'], vmids['BR-RTR'], 'BR-RTR')
run_step("start_BR-RTR_1", start_vm, proxmox, vmids['BR-RTR'])
run_step("create_HQ-SRV", clone_vm, proxmox, vmids['ISP'], vmids['HQ-SRV'], 'HQ-SRV')
run_step("start_HQ-SRV_1", start_vm, proxmox, vmids['HQ-SRV'])
run_step("create_BR-SRV", clone_vm, proxmox, vmids['ISP'], vmids['BR-SRV'], 'BR-SRV')
run_step("start_BR-SRV_1", start_vm, proxmox, vmids['BR-SRV'])
run_step("create_HQ-CLI", clone_vm, proxmox, vmids['ISP'], vmids['HQ-CLI'], 'HQ-CLI')
run_step("start_HQ-CLI_1", start_vm, proxmox, vmids['HQ-CLI'])

# Установка пакетов и удаление их из автозагрузки
# HQ-RTR
run_step("HQ-RTR_install_frr", send_command, proxmox, vmids['HQ-RTR'], ['apt', 'install', 'frr', '-y'])
run_step("HQ-RTR_stop_frr", send_command, proxmox, vmids['HQ-RTR'], ['systemctl', 'stop', 'frr'])
run_step("HQ-RTR_disable_frr", send_command, proxmox, vmids['HQ-RTR'], ['systemctl', 'disable', 'frr'])
run_step("HQ-RTR_install_dnsmasq", send_command, proxmox, vmids['HQ-RTR'], ['apt', 'install', 'dnsmasq', '-y'])
run_step("HQ-RTR_stop_dnsmasq", send_command, proxmox, vmids['HQ-RTR'], ['systemctl', 'stop', 'dnsmasq'])
run_step("HQ-RTR_disable_dnsmasq", send_command, proxmox, vmids['HQ-RTR'], ['systemctl', 'disable', 'dnsmasq'])
run_step("HQ-RTR_install_sshpass", send_command, proxmox, vmids['HQ-RTR'], ['apt', 'install', 'sshpass', '-y'])

# BR-RTR
run_step("BR-RTR_install_frr", send_command, proxmox, vmids['BR-RTR'], ['apt', 'install', 'frr', '-y'])
run_step("BR-RTR_stop_frr", send_command, proxmox, vmids['BR-RTR'], ['systemctl', 'stop', 'frr'])
run_step("BR-RTR_disable_frr", send_command, proxmox, vmids['BR-RTR'], ['systemctl', 'disable', 'frr'])
run_step("BR-RTR_install_sshpass", send_command, proxmox, vmids['BR-RTR'], ['apt', 'install', 'sshpass', '-y'])

# HQ-SRV
run_step("HQ-SRV_install_bind9", send_command, proxmox, vmids['HQ-SRV'], ['apt', 'install', 'bind9', '-y'])
run_step("HQ-SRV_stop_bind9", send_command, proxmox, vmids['HQ-SRV'], ['systemctl', 'stop', 'named'])
run_step("HQ-SRV_disable_bind9", send_command, proxmox, vmids['HQ-SRV'], ['systemctl', 'disable', 'named'])
run_step("HQ-SRV_install_sshpass", send_command, proxmox, vmids['HQ-SRV'], ['apt', 'install', 'sshpass', '-y'])

# BR-SRV
run_step("BR-SRV_install_sshpass", send_command, proxmox, vmids['BR-SRV'], ['apt', 'install', 'sshpass', '-y'])

# HQ-CLI
run_step("HQ-CLI_install_mate_desktop", send_command, proxmox, vmids['HQ-CLI'], ['apt', 'install', 'mate-desktop-environment', '-y'])
run_step("HQ-CLI_install_lightdm", send_command, proxmox, vmids['HQ-CLI'], ['apt', 'install', 'lightdm', '-y'])

# Изменение параметров ВМ
run_step("shutdown_ISP", stop_vm, proxmox, vmids['ISP'])
run_step("ISP_reconf", reconf_vm, proxmox, vmids['ISP'], net1='model=virtio,bridge=ISP_HQ,firewall=1',
          net2='model=virtio,bridge=ISP_BR,firewall=1')
run_step("start_ISP_2", start_vm, proxmox, vmids['ISP'])

run_step("shutdown_HQ-RTR", stop_vm, proxmox, vmids['HQ-RTR'])
run_step("HQ-RTR_reconf", reconf_vm, proxmox, vmids['HQ-RTR'], net0='model=virtio,bridge=ISP_HQ,firewall=1',
          net1='model=virtio,bridge=HQ_SW,firewall=1')
run_step("start_HQ-RTR_2", start_vm, proxmox, vmids['HQ-RTR'])

run_step("shutdown_BR-RTR", stop_vm, proxmox, vmids['BR-RTR'])
run_step("BR-RTR_reconf", reconf_vm, proxmox, vmids['BR-RTR'], net0='model=virtio,bridge=ISP_BR,firewall=1',
          net1='model=virtio,bridge=BR_SW,firewall=1')
run_step("start_BR-RTR_2", start_vm, proxmox, vmids['BR-RTR'])

run_step("shutdown_HQ-SRV", stop_vm, proxmox, vmids['HQ-SRV'])
run_step("HQ-SRV_reconf", reconf_vm, proxmox, vmids['HQ-SRV'], memory=2048,
         net0='model=virtio,bridge=HQ_SW,firewall=1,tag=100')
run_step("start_HQ-SRV_2", start_vm, proxmox, vmids['HQ-SRV'])

run_step("shutdown_BR-SRV", stop_vm, proxmox, vmids['BR-SRV'])
run_step("BR-SRV_reconf", reconf_vm, proxmox, vmids['BR-SRV'], memory=2048,
         net0='model=virtio,bridge=BR_SW,firewall=1')
run_step("start_BR-SRV_2", start_vm, proxmox, vmids['BR-SRV'])

run_step("shutdown_HQ-CLI", stop_vm, proxmox, vmids['HQ-CLI'])
run_step("HQ-CLI_reconf", reconf_vm, proxmox, vmids['HQ-CLI'], memory=3072, cores=2,
         net0='model=virtio,bridge=HQ_SW,firewall=1,tag=200',
          resize=True)
run_step("start_HQ-CLI_2", start_vm, proxmox, vmids['HQ-CLI'])

# Снапшоты
run_step("ISP_snapshot", snap, proxmox, vmids['ISP'])
run_step("HQ-RTR_snapshot", snap, proxmox, vmids['HQ-RTR'])
run_step("BR-RTR_snapshot", snap, proxmox, vmids['BR-RTR'])
run_step("HQ-SRV_snapshot", snap, proxmox, vmids['HQ-SRV'])
run_step("BR-SRV_snapshot", snap, proxmox, vmids['BR-SRV'])
run_step("HQ-CLI_snapshot", snap, proxmox, vmids['HQ-CLI'])

# Создание пользователя и выдача прав
run_step("create_user", create_user, proxmox)
run_step("create_pool", create_pool, proxmox, vmids)
