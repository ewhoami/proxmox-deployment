# Адрес сервера
SERVER = '192.168.0.150'
# Пользователь с правами администратора
USER = 'root@pam'
# Использовать пароль|токен (True|False)
USE_PASSWORD = False
# Token ID (если используется аутентификация через API Token)
API_TOKEN_ID = 'root_token'
# Token value (если используется аутентификация через API Token)
API_TOKEN = 'b4f5b191-ad88-48ac-93c2-96c886799d2f'
# Пароль от пользователя (если используется аутентификация по паролю)
PASSWORD = 'debian123'
# Название node
NODE = 'proxmox'
# Имя хранилища ISO образа
ISO_STORAGE = 'local'
# Имя хранилища дисков виртуальных машин
VM_STORAGE = 'data1'
# Использовать временный HHTP_сервер (True|False)
USE_TEMP_HTTP = True
# Порт временного HTTP-сервера
TEMP_HTTP_SRV_PORT = 8000
# Интерфейс для доступа в интернет, подключаемый к ISP
ISP_INTERFACE = 'vmbr0'
# Имя ISO образа на сервере
ISO_NAME = 'debian-11.11.0-amd64-netinst.iso'
