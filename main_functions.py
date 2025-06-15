from settings import NODE
import time

# Создание VM
def vm_create(server, vmid, name, cores, memory, scsi0, cdrom, net0=None, net1=None, net2=None):
    server.nodes(NODE).qemu.create(vmid=vmid, name=name, cores=cores, memory=memory,
                                   scsi0=scsi0, agent='enabled=1', cdrom=cdrom, net0=net0,
                                   net1=net1, net2=net2)

# Включение ВМ
def start_vm(server, vmid):
    server.nodes(NODE).qemu(vmid).status.start.create()

# Выключение ВМ
def stop_vm(server, vmid):
    server.nodes(NODE).qemu(vmid).status.shutdown.create()

# Создание Network
def net_create(server, name, vlan=False):
    if name not in [net['iface'] for net in server.nodes(NODE).network.get()]:
        if vlan:
            server.nodes(NODE).network.create(iface=name, type='bridge', bridge_vlan_aware=1, autostart=1)
        else:
            server.nodes(NODE).network.create(iface=name, type='bridge', autostart=1)
    else:
        print(f"Network {name} - exists")

# Удаление VM (статические vmid)
def vm_del(server):
    vmids = {
        'ISP': 100,
        'HQ-RTR': 101,
        'BR-RTR': 102,
        'HQ-SRV': 103,
        'BR-SRV': 104,
        'HQ-CLI': 105,
    }
    for vmname in vmids:
        if vmids[vmname] in [vm['vmid'] for vm in server.nodes(NODE).qemu.get()]:
            server.nodes(NODE).qemu(vmids[vmname]).status.stop.create()
            while True:
                if server.nodes(NODE).qemu(vmids[vmname]).status.current.get()['status'] == "stopped":
                    break
                print(f"Stopping VM {vmids[vmname]}...")
                time.sleep(3)
            server.nodes(NODE).qemu(vmids[vmname]).delete()
            print(f"VM {vmids[vmname]} - removed")
        else:
            print(f"VM {vmids[vmname]} not found")

# Удаление Network
def net_del(server):
    nets = ['ISP_HQ', 'ISP_BR', 'HQ_SW', 'BR_SW']
    for network in nets:
        if network in [net['iface'] for net in server.nodes(NODE).network.get()]:
            server.nodes(NODE).network.delete(network)
            if network not in [net['iface'] for net in server.nodes(NODE).network.get()]:
                print(f'Network {network} - removed')
        else:
            print(f'Network {network} not found')

# Отправка команды через qemu-agent (с кодом на выходе)
def send_command(server, vmid, command, return_value=False):
    pid = server.nodes(NODE).qemu(vmid).agent('exec').create(command=command)
    while True:
        result = server.nodes(NODE).qemu(vmid).agent('exec-status').get(pid=pid['pid'])
        if result.get('exited'):
            if return_value:
                return result.get('exitcode')
            else:
                print(f"Exit code: {result.get('exitcode')}")
                break
        time.sleep(1)

# Отправка команды через qemu-agent (с выводом)
def send_command_output(server, vmid, command):
    pid = server.nodes(NODE).qemu(vmid).agent('exec').create(command=command)
    while True:
        result = server.nodes(NODE).qemu(vmid).agent('exec-status').get(pid=pid['pid'])
        if result.get('exited'):
            return result.get('out-data')
        time.sleep(1)

# Клонирование VM
def clone_vm(server, svmid, tvmid, name):
    task = server.nodes(NODE).qemu(svmid).clone.create(newid=tvmid, name=name, full=1)
    while True:
        status = server.nodes(NODE).tasks(task).status.get()
        if status['status'] == 'stopped':
            exitstatus = status.get("exitstatus", "")
            print(f"Exit status: {exitstatus}")
            break

# Изменение параметоров VM
def reconf_vm(server, vmid, memory=None, cores=None, net0=None, net1=None, net2=None, resize=False):
    while server.nodes(NODE).qemu(vmid).status.current.get()['status'] == "stopped":
        dots = (dots % 3) + 1
        print(f"\rWaiting for VM shutdown{'.' * dots} ", end='')
        time.sleep(1)
    if memory != None:
        server.nodes(NODE).qemu(vmid).config.create(memory=memory)
    if cores != None:
        server.nodes(NODE).qemu(vmid).config.create(cores=cores)
    if net0 != None:
        server.nodes(NODE).qemu(vmid).config.create(net0=net0)
    if net1 != None:
        server.nodes(NODE).qemu(vmid).config.create(net1=net1)
    if net2 != None:
        server.nodes(NODE).qemu(vmid).config.create(net2=net2)
    if resize:
        server.nodes(NODE).qemu(vmid).resize.set(disk='scsi0', size='15G')

# Создание снапшота
def snap(server, vmid):
    server.nodes(NODE).qemu(vmid).snapshot.create(snapname="INIT")

# Создание пользователя
def create_user(server):
    if 'module-1@pve' not in [user['userid'] for user in server.access.users.get()]:
        server.access.users.create(userid='module-1@pve', password='module-1')

# Создание пула
def create_pool(server, vmids):
    if 'module-1' not in [pool['poolid'] for pool in server.pools.get()]:
        server.pools.create(poolid='module-1')
        server.pools('module-1').set(vms=f"{vmids['ISP']},{vmids['HQ-RTR']},"
                                          f"{vmids['BR-RTR']},{vmids['HQ-SRV']},"
                                          f"{vmids['BR-SRV']},{vmids['HQ-CLI']}")
        server.access.acl.set(path='/pool/module-1',
                               users='module-1@pve',
                               roles='PVEVMAdmin')

# Проверка Hostname, timezone и интерфейсов
def base_check(server, vmname, vmid, file):
    file.write(f"{vmname}:\n")
    file.write("\thostname:\n")
    file.write(f"\t\t{server.nodes(NODE).qemu(vmid).agent.get('get-host-name')['result']['host-name']}\n")
    file.write("\tTime zone:\n")
    for line in send_command_output(server, vmid, ['timedatectl', 'status']).splitlines():
        if "Time zone:" in line:
            file.write(f"\t\t{' '.join(line.split()[2:])}\n")
    file.write("\tinterfaces:\n")
    for interface in server.nodes(NODE).qemu(vmid).agent.get('network-get-interfaces')['result']:
        if 'ip-addresses' in interface:
            if interface['name'] != 'lo':
                if interface['ip-addresses'][0]['ip-address-type'] != 'ipv6':
                    file.write(
                        f"\t\t{interface['name']} - {interface['ip-addresses'][0]['ip-address']}/"
                        f"{interface['ip-addresses'][0]['prefix']}\n")

# Проверка ip_forward
def ipf_check(server, vmid, file):
    file.write("\tip_forward:\n")
    ipf = send_command_output(server, vmid, ['sysctl', '-p'])
    if ipf and ('ip_forward=1' in ipf):
            file.write(f"\t\tspecified")
    else:
        file.write('\t\tnot specified\n')

# Проверка iptables (nat)
def iptables_check(server, vmid, file):
    file.write("\tiptables:\n")
    for line in send_command_output(server, vmid, ['iptables', '-t', 'nat', '-S']).splitlines():
        file.write(f"\t\t{line}\n")

# Проверка gre
def gre_check(server, vmid, file):
    file.write("\tgre:\n")
    gre = send_command_output(server, vmid, ['ip', 'a', 'show', 'gre1'])
    if gre:
        for line in gre.splitlines():
            file.write(f"\t\t{line}\n")

# Проверка net_admin
def na_check(server, vmid, file):
    file.write("\tnet_admin:\n")
    user = send_command_output(server, vmid, ['grep', 'net_admin', '/etc/passwd'])
    if user:
        file.write("\t\tExists\n")
    file.write("\tsudo:\n")
    sudo = send_command_output(server, vmid, ['grep', 'net_admin', '/etc/sudoers'])
    if sudo:
        file.write(f"\t\t{sudo}")
    file.write("\tP@$$word test (port 22):\n")
    send_command(server, vmid, ['systemctl', 'enable', 'ssh'], return_value=True)
    send_command(server, vmid, ['systemctl', 'start', 'ssh'], return_value=True)
    if not send_command(server, vmid,
                        ['sshpass', '-p', 'P@$$word', 'ssh', '-p', '22', '-o', 'StrictHostKeyChecking=no',
                         'net_admin@localhost'], return_value=True):
        file.write("\t\tOK\n")
    else:
        file.write("\t\tFailed\n")
    send_command(server, vmid, ['systemctl', 'disable', 'ssh'], return_value=True)
    send_command(server, vmid, ['systemctl', 'stop', 'ssh'], return_value=True)

# Проверка frr
def frr_check(server, vmid, file):
    file.write("\tfrr:\n")
    for line in send_command_output(server, vmid, ['cat', '/etc/frr/frr.conf']).splitlines():
        file.write(f"\t\t{line}\n")

# Проверка dnsmasq
def dnsmasq_check(server, vmid, file):
    file.write("\tdnsmasq:\n")
    dnsmasq_conf = send_command_output(server, vmid, ['cat', '/etc/dnsmasq.conf'])
    for line in dnsmasq_conf.splitlines():
        if (not line.startswith('#')) and (line != ''):
            file.write(f"\t\t{line}\n")

# Проверка ssh (sshuser)
def ssh_check(server, vmid, file):
    file.write("\tssh:\n")
    ssh = send_command_output(server, vmid, ['cat', '/etc/ssh/sshd_config.d/demo.conf'])
    banner_path = None
    if ssh:
        for line in ssh.splitlines():
            if "Banner" in line:
                banner_path = line.split()[1]
            file.write(f"\t\t{line}\n")
    file.write("\tbanner:\n")
    if banner_path:
        file.write(f"\t\t{send_command_output(server, vmid, ['cat', banner_path])}")
    file.write("\tsshuser:\n")
    uid = send_command_output(server, vmid, ['grep', 'sshuser', '/etc/passwd'])
    if uid:
        file.write(f"\t\tUID - {uid.split(':')[2]}\n")
    file.write("\tsudo:\n")
    sudo = send_command_output(server, vmid, ['grep', 'sshuser', '/etc/sudoers'])
    if sudo:
        file.write(f"\t\t{sudo}")
    file.write("\tP@ssw0rd test (port 2024):\n")
    if not send_command(server, vmid,
                        ['sshpass', '-p', 'P@ssw0rd', 'ssh', '-p', '2024', '-o', 'StrictHostKeyChecking=no',
                         'sshuser@localhost'], return_value=True):
        file.write("\t\tOK\n")
    else:
        file.write("\t\tFailed\n")

# Проверка режима интерфейса (ens18)
def iface_mode_check(server, vmid, file):
    file.write("\tinterface mode:\n")
    iface_mode = send_command_output(server, vmid, ['grep', 'iface', '/etc/network/interfaces'])
    for line in iface_mode.splitlines():
        if 'loopback' not in line:
            file.write(f"\t\t{line}\n")

# nslookup
def nslookup(server, vmid, domain_names, file):
    file.write("\tnslookup:\n")
    for name in domain_names:
        file.write(f"\t\t{name}:\n")
        for line in send_command_output(server, vmid, ['nslookup', '-timeout=2', name]).splitlines():
            file.write(f"\t\t\t{line}\n")
