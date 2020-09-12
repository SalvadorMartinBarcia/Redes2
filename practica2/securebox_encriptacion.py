from Crypto.Cipher import AES, PKCS1_v1_5, PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad
from Crypto.Signature import pkcs1_15
import os
import time

## firma
#  Args:
#  mensaje: texto del archivo a firmar
#
#  Funcionalidad: Devuelve una cadena segun el error recibido
def firma(mensaje):
    print('-> Firmando fichero...', end='')
    #https://pycryptodome.readthedocs.io/en/latest/src/hash/sha256.html

    #Se realiza un hash del mensaje
    h = SHA256.new(mensaje)
    
    #https://pycryptodome.readthedocs.io/en/latest/src/examples.html
    #Abre la clave privada RSA del fichero
    secret_code = "Unguessable"
    encoded_key = open("keys/rsa_private_key.bin", "rb").read()
    claveRSA = RSA.import_key(encoded_key, passphrase=secret_code)

    #https://pycryptodome.readthedocs.io/en/latest/src/cipher/pkcs1_v1_5.html
    #Firma el hash usando la clave RSA
    cipher = PKCS1_v1_5.new(claveRSA)
    firma = pkcs1_15.new(claveRSA).sign(h)

    #Guarda en un archivo temporal la firma y el mensaje concatenados
    x = firma + mensaje
    salida = open('tmp/firma.dat', "wb")
    salida.write(x)
    salida.close()
    print('OK')


## encriptar
#  Args:
#  filename: ubicacion del archivo a firmar
#  clavePublica: clave publica del usuario destino
#
#  Funcionalidad: Devuelve una cadena segun el error recibido
def encriptar(filename, clavePublica):
    print('-> Cifrando fichero...', end='')
    #Abre el archivo
    try:
        archivo = open(filename, "rb")
        mensaje = archivo.read()
        archivo.close()
    except FileNotFoundError:
        print('Error, el fichero no existe o no es accesible')
        return -3

    #Genera un vector de inicializacion y una clave aleatorio
    iv = get_random_bytes(16)
    clave = get_random_bytes(32)
    #Ciframos la clave aleatoria de 256 bits usando iv
    cipher = AES.new(clave,AES.MODE_CBC,iv)

    #evitamos ValueError: Data must be padded to 16 byte boundary in CBC mode con esta linea
    mensaje = pad(mensaje, 16)

    #Encriptamos el fichero
    msgCifrado = cipher.encrypt(mensaje)
    
    #Abrimos la clave publica del receptor y encriptamos con esta la clave
    rsaReceptor = RSA.import_key(clavePublica)
    funcionRSA = PKCS1_OAEP.new(rsaReceptor)

    claveCifrada = funcionRSA.encrypt(clave)

    msgEncriptado = iv + claveCifrada + msgCifrado

    #volcamos esto en un archivo:

    nombreFichero = filename + '_cifrado'
    archivo = open(nombreFichero, "wb")
    archivo.write(msgEncriptado)
    archivo.close()


    print('OK')

    return msgEncriptado 
    
## encriptar
#  Args:
#  filename: nombre del archivo a firmar
#  clavePublica: clave publica del usuario destino
#
#  Funcionalidad: Devuelve una cadena segun el error recibido
def encriptaFirma(filename, clavePublica):
    #Abre el archivo, no encriptado ni firmado
    try:
        archivo = open(filename, "rb")
        contenido = archivo.read()
        archivo.close()
    except FileNotFoundError:
        print('Error, el fichero no existe o no es accesible')
        return -3
    #Firma el archivo
    firmado = firma(contenido)
    #Espera unos segundos por si hay retrasos al crear el firma.dat
    time.sleep(2)
    #Encripta el archivo
    encriptar("tmp/firma.dat", clavePublica)
    #El archivo temporal cifrado es renombrado y movido a la carpeta de archivos
    try:
        os.rename('tmp/firma.dat_cifrado', 'files/'+ filename + '_cifrado')
    except FileExistsError:
        os.remove('files/'+ filename + '_cifrado')
        os.rename('tmp/firma.dat_cifrado', 'files/'+ filename + '_cifrado')
    os.remove('tmp/firma.dat')
    return 'files/'+ filename + '_cifrado'

## generarRSA
#  
#  Funcionalidad: Genera un par de claves RSA y las guarda en ./keys/
def generarRSA():
    #Genera clave publica y privada y las guarda
    #https://pycryptodome.readthedocs.io/en/latest/src/examples.html#generate-an-rsa-key
    secret_code = "Unguessable"
    key = RSA.generate(2048)
    print("Generando par de claves RSA de 2048 bits...",end='')
    encrypted_key = key.export_key('PEM')
    file_out = open("keys/rsa_private_key.bin", "wb")
    file_out.write(encrypted_key)
    file_out.close()
    
    pk = key.publickey().export_key('PEM')
    file_out = open("keys/rsa_public_key.bin", "wb")
    file_out.write(pk)
    file_out.close()
    
    print("OK")
    return

## desencriptar
#  Args:
#  nombreFichero: nombre del archivo a desencriptar
#  usuario: id del usuario que envio el archivo
#
#  Funcionalidad: Desencripta un archivo y lo guarda en la carpeta ./downloads
def desencriptar(nombreFichero, usuario):

    print('-> Descifrando fichero...', end='')
    #Abre el fichero descargado previamente
    fichero = open('tmp/' + nombreFichero, 'rb')
    contenido = fichero.read()
    fichero.close()

    #Divide el contenido en sus partes
    iv = contenido[0:16]
    clave = contenido[16:256+16]
    msgFirma = contenido[256+16:]


    #Abre la clave privada del usuario
    secret_code = "Unguessable"
    encoded_key = open("keys/rsa_private_key.bin", "rb").read()
    claveRSA = RSA.import_key(encoded_key, passphrase=secret_code)

    #Desencripta la clave usando la clave privada
    #https://pycryptodome.readthedocs.io/en/latest/src/examples.html#encrypt-data-with-rsa
    cipher_rsa = PKCS1_OAEP.new(claveRSA)
    clave = cipher_rsa.decrypt(clave)

    #Usando la clave desencripta el mensaje y el sobre digital
    #https://pycryptodome.readthedocs.io/en/latest/src/examples.html#encrypt-data-with-aes
    cipher = AES.new(clave, AES.MODE_CBC, iv)
    data = cipher.decrypt(msgFirma)
    #Deshacemos el padding que tuvimos que hacer
    data = unpad(data, 16)

    #Separamos la firma del contenido
    firma = data[0:256]
    contenido = data[256:]
    print('OK')

    print('-> Verificando firma...', end='')
    #Hacemos el hashing del contenido del fichero
    h = SHA256.new(contenido)

    #Comprobamos que el hashing esta hecho correcto
    #https://pycryptodome.readthedocs.io/en/latest/src/signature/pkcs1_v1_5.html
    claveEmisor = RSA.import_key(usuario)
    try:
        pkcs1_15.new(claveEmisor).verify(h, firma)

    except (ValueError, TypeError):
        print("Error, La firma del fichero no coincide con la clave publica del usuario")
        return
    print('OK')
    salida = open('downloads/' + nombreFichero, "wb")
    salida.write(contenido)
    salida.close()

    try:
        os.remove('tmp/' + nombreFichero)
    except FileNotFoundError:
        print()
    print('Fichero ' + nombreFichero + ' descargado y verificado correctamente  ')