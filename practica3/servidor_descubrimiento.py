import socket
import sys

#Extraemos la tupla IP/puerto del archivo de configuracion
config = open('./config.conf', 'r')
server_ip = config.readlines(1)
server_ip = str(server_ip)[17:-4]

server_port = config.readlines(2)
server_port = str(server_port)[14:18]
config.close()

server_address = (server_ip, int(server_port))


# Protocolos soportados por esta aplicación
protocol = 'v0'

BUFF = 4096
## register
#  Args:
#  user: Usuario que inicia sesión
#  password: Contraseña del usuario que inicia sesión
#  ip: Ip donde el usuario quiere recibir la comunicación
#  port: Puerto donde el usuario quiere recibir la comunicación
#
#  Funcionalidad: Registra al usuario en el servidor de descubrimiento
def register(user, password, ip, port):
    #if((user == None) | (password == None) | (ip == None) | (port == None) | (protocol == None)):
    if not (user and password and ip and port and protocol):
        return "NOK"
    #Esto es python, no C o si quieres aplicas demorgan pero no hagas cosas tan feas
    #if not user or not password or not ip or not port or not protocol: Por ejemplo, no se
    msg = 'REGISTER ' + user + ' ' + ip + ' '  + port + ' '  + password + ' ' + protocol

    response = send_server(msg)

    if response == "NOK WRONG_PASS":
        return "NOK"
    else:
        return "OK"

## query
#  Args:
#  nick: Nombre del usuario
#
#  Funcionalidad: Dado un nombre de usario retorna todos sus datos si esta registrado
def query(nick):
    if not nick:
        return None

    msg = 'QUERY ' + nick

    response = send_server(msg)

    response_split = response.split(' ')
    if response_split[0] == 'OK':
        user = {}
        user['nick'] = response_split[2]
        user['ip'] = response_split[3]
        user['port'] = response_split[4]
        user['protocol'] = response_split[5]

        return user
    else:
        return None

## list_users
#  Args:
#
#  Funcionalidad: Lista a todos los usuarios del servidor de descubrimiento
def list_users():
    msg = 'LIST_USERS'

    response = send_server(msg)

    response_split = response.split(' ')
    if response_split[0] == 'NOK':
        return None

    response_split = response.split('#')

    user = response_split[0].split(' ')
    msg = user[3] + ' ' + user[4] + ':' + user[5] + '\n'

    response_split = response_split[1:]
    for u in response_split:
        user = u.split(' ')
        if len(user) == 4:
            msg += user[0] + ' ' + user[1] + ':' + user[2] + '\n'
    return msg

## list_users
#  Args:
#
#  Funcionalidad: Termina la conexión con el servidor
def quit(sock):
    msg = 'QUIT'
    
    sock.sendall(msg.encode())
    response = sock.recv(BUFF)

## list_users
#  Args:
#  msg: Mensaje que queremos enviar
#
#  Funcionalidad: Envia el mensaje dado al servidor de descubrimiento
def send_server(msg):
    serversock = socket.socket()
    serversock.connect(server_address)

    serversock.sendall(msg.encode())
    response = serversock.recv(BUFF).decode()
    quit(serversock)
    serversock.close()
    return response