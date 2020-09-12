## paquete securebox_client
#  Implementa la interfaz de la aplicación
#  Autores: Salvador Martin, Dan Roife 


#Para el paso de argumentos
import sys
#Para el envio de peticiones HTTP https://requests.readthedocs.io/en/master/
import requests
#Para borrar directorios completos (comando clean)
import shutil
#Para procesar peticiones
import json

import ast

#Para utilizar la funcionalidad implementada
from securebox_usuarios import *
from securebox_encriptacion import *
from securebox_archivos import *

#Para administrar los argumentos de entrada
import argparse


#argumentos de entrada https://docs.python.org/3/library/argparse.html
parser = argparse.ArgumentParser(description='Opciones disponibles')
parser.add_argument('--create_id', metavar=('nombre', 'email'), nargs=2,
                   help='Crea una nueva identidad (par de claves púlica y privada) para un usuario con nombre nombre y correo email, y la registra en SecureBox, para que pueda ser encontrada por otros usuarios. alias es una cadena identificativa opcional.')
parser.add_argument('--search_id', metavar='cadena', nargs=1,
                   help='Busca un usuario cuyo nombre o correo electrónico contenga cadena en el repositorio de identidades de SecureBox, y devuelve su ID.')
parser.add_argument('--delete_id', metavar='id', nargs=1,
                   help='Borra la identidad con ID id registrada en el sistema. Obviamente, sólo se pueden borrar aquellas identidades creadas por el usuario que realiza la llamada.')
parser.add_argument('--upload', metavar='fichero', nargs=1,
                   help='Envia un fichero a otro usuario, cuyo ID es especificado con la opción --dest_id. Por defecto, el archivo se subirá a SecureBox firmado y cifrado con las claves adecuadas para que pueda ser recuperado y verificado por el destinatario.')
parser.add_argument('--source_id', metavar='source_id', nargs=1,
                   help='ID del emisor del fichero.')
parser.add_argument('--dest_id', metavar='dest_id', nargs=1,
                   help='ID del receptor del fichero.')
parser.add_argument('--list_files', action='store_true',
                   help='Lista todos los ficheros pertenecientes al usuario.')
parser.add_argument('--download', metavar='id_fichero', nargs=1,
                   help='Recupera un fichero con ID id_fichero del sistema (este ID se genera en la llamada a upload, y debe ser comunicado al receptor). Tras ser descargado, debe ser verificada la firma y, después, descifrado el contenido.')
parser.add_argument('--delete_file', metavar=' id_fichero', nargs=1,
                   help='Borra un fichero del sistema.')
parser.add_argument('--encrypt', metavar='fichero', nargs=1,
                   help='Cifra un fichero, de forma que puede ser descifrado por otro usuario, cuyo ID es especificado con la opción --dest_id.')
parser.add_argument('--sign', metavar='fichero', nargs=1,
                   help='Firma un fichero.')
parser.add_argument('--enc_sign', metavar='fichero', nargs=1,
                   help='Cifra y firma un fichero, combinando funcionalmente las dos opciones anteriores.')
parser.add_argument('--clean', action='store_true',
                   help='Elimina todos los archivos encriptados y descargados.')

args = parser.parse_args()

#sys.argv[1] = argumento de entrada
#Si esta vacio imprimimos lista de posibles comandos (lista generada por argparse automaticamente)
if len(sys.argv) < 2:
    parser.print_usage()
    sys.exit(1)

#Creamos los directorios necesarios para usar el programa si no existieran:
#Aqui se guardaran los archivos descargados
if not os.path.isdir('./downloads'):
    try:
        os.mkdir('./downloads')
    except OSError:
        print('Error al generar los directorios necesarios, asegurese de que el programa puede modificar directorios')
#Aqui se guardaran los archivos intermedios pendientes de encriptar o desencriptar
if not os.path.isdir('./tmp'):
    try:
        os.mkdir('./tmp') 
    except OSError:
        print('Error al generar los directorios necesarios, asegurese de que el programa puede modificar directorios')
#Aqui se guardaran los archivos encriptados
if not os.path.isdir('./files'):
    try:
        os.mkdir('./files')
    except OSError:
        print('Error al generar los directorios necesarios, asegurese de que el programa puede modificar directorios')
#Aqui se guardaran las claves RSA una vez generadas
if not os.path.isdir('./keys'):
    try:
        os.mkdir('./keys')
    except OSError:
        print('Error al generar los directorios necesarios, asegurese de que el programa puede modificar directorios')



#Extraemos la URL y el token del fichero de configuracion
config = open('./config.conf', 'r')
server_url=config.readlines(1)
server_url=str(server_url)[13:44]

auth_token=config.readlines(2)
auth_token=str(auth_token)[13:36]
config.close()

#Declaramos los endpoints en un diccionario por comodidad
endpoints= {
        "user_register": "/users/register" ,
        "user_publicKey": "/users/getPublicKey" ,
        "user_search": "/users/search" ,
        "user_delete": "/users/delete" ,

        "file_upload": "/files/upload" ,
        "file_download": "/files/download" ,
        "file_list": "/files/list" ,
        "file_delete": "/files/delete" 
}
#Guardamos tambien la cabecera de autorizacion:
header={'Authorization' : auth_token}


#Una vez tenemos todo esto listo empezamos a procesar los comandos del usuario

#2.1 Gestion de identidades y usuarios


#--create_id nombre email [alias]
if args.create_id:
    url = server_url + endpoints["user_register"]
    crear_usuario(args.create_id[0], args.create_id[1], url, header)
    
#--search_id cadena
if args.search_id:
    url = server_url + endpoints["user_search"]
    buscar_usuario(args.search_id[0], url, header)

#--delete_id id
if args.delete_id:
    url = server_url + endpoints["user_delete"]
    borrar_usuario(args.delete_id[0], url, header)


# #2.2 Cifrado y firma de archivos

# #--encrypt fichero
if args.encrypt:
    if not args.dest_id:
        print("Introduce la ID del usuario al que deseas enviarle el fichero con el argumento --dest_id")
        sys.exit(0)

    url = server_url + endpoints["user_publicKey"]
    clave = clavePublica(args.dest_id[0], url, header)
    if clave == None:
        sys.exit(0)
        
    encriptar(args.encrypt[0], clave)

# #--sign fichero
# if sys.argv[1] == '--sign':
if args.sign:
    if not args.dest_id:
        print("Introduce la ID del usuario al que deseas enviarle el fichero con el argumento --dest_id")
        sys.exit(0)

    url = server_url + endpoints["user_publicKey"]
    clave = clavePublica(args.dest_id[0], url, header)
    if clave == None:
        sys.exit(0)
        
    try:
        archivo = open(args.sign[0], "rb")
        mensaje = archivo.read()
        archivo.close()
    except FileNotFoundError:
        print('Error al abrir el archivo')
        sys.exit(0)

    firma(mensaje)

# #--enc_sign fichero
# if sys.argv[1] == '--enc_sign':
if args.enc_sign:
    if not args.dest_id:
        print("Introduce la ID del usuario al que deseas enviarle el fichero con el argumento --dest_id")
        sys.exit(0)
    
    url = server_url + endpoints["user_publicKey"]
    clave = clavePublica(args.dest_id[0], url, header)
    if clave == None:
        sys.exit(0)
        
    encriptaFirma(args.enc_sign[0], clave)


# #2.3. Envío y descarga de ficheros

# #--upload fichero
if args.upload:

    if not args.dest_id: #Sin ID de destino no se puede encriptar
        print("Introduce la ID del usuario al que deseas enviarle el fichero con el argumento --dest_id")
        sys.exit(0)
    print('Solicitado envio de fichero a SecureBox')
    url = server_url + endpoints["user_publicKey"]
    clave = clavePublica(args.dest_id[0], url, header)
    if clave == None:
        sys.exit(0)

    fichero = encriptaFirma(args.upload[0], clave)

    url = server_url + endpoints["file_upload"]
    subidaArchivo(fichero, url, header)


# #--list_files
if args.list_files:
    url = server_url + endpoints["file_list"]
    listaArchivos(url, header)


# #--download id_fichero
if args.download:
    if not args.source_id: #Sin ID de emisor no se puede desencriptar
        print("Introduce la ID del usuario ha emitido el fichero con el argumento --source_id")
        sys.exit(0)
    url = server_url + endpoints["user_publicKey"]
    clave = clavePublica(args.source_id[0], url, header)
    
    url = server_url + endpoints["file_download"]
    bajadaArchivo(args.download[0], clave ,url, header)


# #--delete_file id_fichero
if args.delete_file:
    url = server_url + endpoints["file_delete"]
    borraArchivo(args.delete_file[0], url, header)

# #--clean
#Elimina todos los archivos generados por la aplicacion
if args.clean:
    shutil.rmtree('downloads/')
    shutil.rmtree('files/')

#Eliminamos los archivos temporales residuales
shutil.rmtree('tmp/')