import sys
import requests
import json
import datetime
from securebox_encriptacion import desencriptar


## subidaArchivo
#  Args:
#  fichero: fichero a subir
#  url: url del servidor + endpoint
#  header: cabecera para enviar con la peticion HTTP
#
#  Funcionalidad: Sube un archivo al servidor
def subidaArchivo(fichero, url, header):
    print('-> Subiendo fichero a servidor...', end='')
    #Si es posible abre el archivo
    try:
        archivo = open(fichero, "rb")
        
    except FileNotFoundError:
        print('Error al abrir el archivo para subir')
        sys.exit(0)
    
    args= {'ufile': archivo}

    #Envia la peticion
    try:
        r = requests.post(url, files = args, headers = header)
    #https://requests.readthedocs.io/en/master/user/quickstart/#errors-and-exceptions
    except requests.ConnectionError:
        print("Error al intentar establecer conexion con el servidor")
        return -1

    response = json.loads(r.text)

    if r.status_code != 200:
        sys.exit(procesaError(response['error_code']))

    print('Subida realizada correctamente, ID del fichero: ' + response["file_id"])
    archivo.close()
    print('OK')

## listaArchivos
#  Args:
#  url: url del servidor + endpoint
#  header: cabecera para enviar con la peticion HTTP
#
#  Funcionalidad: Imprime por pantalla una lista con todos los archivos
def listaArchivos(url, header):
    #Realiza la peticion
    try:
        r = requests.post(url, headers = header)
    #https://requests.readthedocs.io/en/master/user/quickstart/#errors-and-exceptions
    except requests.ConnectionError:
        print("Error al intentar establecer conexion con el servidor")
        return -1

    response = json.loads(r.text)
    if r.status_code != 200:
        sys.exit(procesaError(response['error_code']))

    #Si se encuentran archivos imprime una lista con los nombres y las ID de estos por pantalla
    print('Se han encontrado ' + str(response['num_files']) +' archivos:\n')
    for archivo in response["files_list"]:
        print('Archivo: ' + archivo['fileName']+'; ID: ' + archivo['fileID'])
## subidaArchivo
#  Args:
#  id: id del archivo a eliminar
#  url: url del servidor + endpoint
#  header: cabecera para enviar con la peticion HTTP
#
#  Funcionalidad: Elimina un fichero del servidor
def borraArchivo(id, url, header):

    #Realiza la peticion
    args= {'file_id': id}
    try:
        r = requests.post(url, headers = header, json=args)
    #https://requests.readthedocs.io/en/master/user/quickstart/#errors-and-exceptions
    except requests.ConnectionError:
        print("Error al intentar establecer conexion con el servidor")
        return -1
    response = json.loads(r.text)
    if r.status_code != 200:
        sys.exit(procesaError(response['error_code']))
    
    print('Archivo con ID: '+ response["file_id"] +' borrado con exito')

## subidaArchivo
#  Args:
#  id: id del fichero a descargar
#  usuario: id del usuario que subio el archivo (id_source)
#  url: url del servidor + endpoint
#  header: cabecera para enviar con la peticion HTTP
#
#  Funcionalidad: Sube un archivo al servidor
def bajadaArchivo(id, usuario ,url, header):

    print('-> Descargando fichero de SecureBox...', end='')
    #Realiza la peticion
    args= {'file_id': id}
    try:
        r = requests.post(url, headers = header, json=args)
    #https://requests.readthedocs.io/en/master/user/quickstart/#errors-and-exceptions
    except requests.ConnectionError:
        print("Error al intentar establecer conexion con el servidor")
        return -1
    if r.status_code != 200:
        sys.exit(procesaError(response['error_code']))

    #Guarda como cadena la fecha actual
    now = datetime.datetime.now()
    nombreFichero = (str(now.year) + '_' + str(now.month) + '_' + str(now.day) + '_' + str(now.hour) + '_' + str(now.minute) + '_' + str(now.second))

    #Vuelca el contenido de la respuesta en un archivo llamado como la fecha
    archivo = open('tmp/' + nombreFichero, "wb")
    archivo.write(r.content)
    archivo.close()
    print('OK')
    print('-> ' + str(len(r.content)) + ' bytes descargados correctamente')
    #Llama a la funcion para desencriptar el archivo
    desencriptar(nombreFichero, usuario)

## procesaError
#  Args:
#  error_code: codigo de error de la respuesta
#
#  Funcionalidad: Devuelve una cadena segun el error recibido
def procesaError(error_code):
    if error_code == 'FILE1':
        print('Error, Se ha supera el tamaño máximo permitido en la subida de un fichero (50Kb)')
    elif error_code == 'FILE2':
        print('Error, El ID de fichero proporcinado no es correcto (el fichero no existe o el usuario no disponde permisos para acceder a él)')
    elif error_code == 'FILE3':
        print('Error , Se ha supera el tamaño máximo permitido en la subida de un fichero (50Kb)')
    elif error_code == 'TOK1':
        print('Error, Token de usuario incorrecto.')
    elif error_code == 'TOK2':
        print('Error, Token de usuario caducado, se debe solicitar uno nuevo.')
    elif error_code == 'TOK3':
        print('Error, Falta cabecera de autenticación. No se ha incluido la cabecera o ésta tiene un forma incorrecto.')
    elif error_code == 'USER_ID1':
        print('Error, El ID  de usuario proporcionado no existe.')
    elif error_code == 'USER_ID2':
        print('Error, No se ha encontrado el usuario con los datos proporcionados para la búsqueda con la función search.')
    elif error_code == 'ARGS1':
        print('Error, Los argumentos de la petición HTTP son erróneos.')   
    else:
        print('Error desconocido ')

    return -2