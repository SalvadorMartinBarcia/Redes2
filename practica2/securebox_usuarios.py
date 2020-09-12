#Generar claves RSA
from securebox_encriptacion import generarRSA
#Funcion generica para control de errores de respuesta
from securebox_archivos import procesaError
#RSA 
from Crypto.PublicKey import RSA
#Usado para terminar sin devolver (sys.exit)
import sys
#Procesamiento de peticiones http
import requests
#Procesamiento de respuestas en JSON
import json

## crear_usuario
#  Args:
#  nombre: nombre del usuario a crear (cualquier string es suficiente)
#  email: email del usuario a crear (cualquier string es suficiente)
#  url: url del servidor + endpoint
#  header: cabecera para enviar con la peticion HTTP
#
#  Funcionalidad: Genera un par de claves RSA y registra a un usuario
#                 en securebox subiendo su clave publica.
def crear_usuario(nombre, email, url, header):

    #Genera la clave RSA
    generarRSA()

    #Abre el fichero donde se encuentra la clave pública y la añade a los argumentos
    f = open('keys/rsa_public_key.bin', 'rb')
    clave_publica = RSA.import_key(f.read())
    f.close()
    clave_publica = clave_publica.export_key('OpenSSH').decode('utf-8')

    args= {'nombre': nombre, 'email': email, 'publicKey': clave_publica}

    #Envia la peticion HTTP
    try:
        r = requests.post(url, json = args, headers = header)
    #https://requests.readthedocs.io/en/master/user/quickstart/#errors-and-exceptions
    except requests.ConnectionError:
        print("Error al intentar establecer conexion con el servidor")
        return -1
    
    response = json.loads(r.text)
    if r.status_code != 200:
        sys.exit(procesaError(response['error_code']))
    
    print('Identidad con ID' + '#' + response['userID'] +' creada correctamente')
    return 1

## buscar_usuario
#  Args:
#  cadena: cadena a buscar (cualquier string es suficiente)
#  url: url del servidor + endpoint
#  header: cabecera para enviar con la peticion HTTP
#
#  Funcionalidad: Busca una cadena en securebox y imprime los resultados
#                 encontrados por pantalla
def buscar_usuario(cadena, url, header):
    print("Buscando usuario '"+ cadena+"' em el servidor...",end='')

    #Realiza la peticion
    args = {'data_search': cadena}
    try:
        r = requests.post(url, json=args, headers=header)
        print("OK")
    except requests.ConnectionError:
        print("Error al intentar establecer conexion con el servidor")
        return -1

    response = json.loads(r.text)
    
    if r.status_code != 200:
        sys.exit(procesaError(response['error_code']))
    i = 1

    #Si se han encontrado resultados (len>1) los imprime por pantalla
    if len(response) > 1:
        print(str(len(response)) + " usuarios encontrados:")
        for user in response:
            nombre = str(user["nombre"])
            email = str(user["email"])
            userID = str(user["userID"])
            print("["+ str(i) + "] " + nombre + ", " + email + ", " + userID )
            i = i + 1
    else:
        print("No se han encontrado usuarios con la cadena "+ cadena)

    return 1
## borrar_usuario
#  Args:
#  id: id del usuario a eliminar
#  url: url del servidor + endpoint
#  header: cabecera para enviar con la peticion HTTP
#
#  Funcionalidad: Elimina un usuario
def borrar_usuario(id, url, header):

    #Envia la peticion HTTP
    args = {'userID': id}
    print("Solicitando borrado de la identidad #" + id +"...", end="")
    try:
        r = requests.post(url, json=args, headers=header)
        print("OK")
    except requests.ConnectionError:
        print("Error al intentar establecer conexion con el servidor")
    response = json.loads(r.text)
    if r.status_code != 200:
        sys.exit(procesaError(response['error_code']))
    print("Identidad con ID#" + response["userID"]+" borrada correctamente" )

## buscar_usuario
#  Args:
#  id: id del usuario del que se quiere conocer la clave
#  url: url del servidor + endpoint
#  header: cabecera para enviar con la peticion HTTP
#
#  Funcionalidad: Devuelve la clave publica de un usuario de securebox
def clavePublica(id, url, header):
    print('-> Recuperando clave pública de ID' + id + '...', end="")
    #Envia la peticion
    args = {'userID': id}

    try:
        r = requests.post(url, json=args, headers=header)

    except requests.ConnectionError:
        print("Error al intentar establecer conexion con el servidor")
        return -1
        
    response = json.loads(r.text)
    if r.status_code != 200:
        sys.exit(procesaError(response['error_code']))

    if response["publicKey"] == None:
        print('Error al obtener la clave publica del usuario')
        return None

    print("OK")
    return response["publicKey"]