
import json
import os
import shutil

global inCall
global hold
global on

inCall = False
on = True
hold = False

## write_user_log
#  Args:
#  user_log: diccionario con la informacion del usuario
#
#  Funcionalidad: Guarda la informacion del usuario logueado
#  en un fichero json

def write_user_log(user_log):
    # Creamos el directorio donde van a ir los usuarios
    if not os.path.isdir('./tmp'):
        try:
            os.mkdir('./tmp') 
        except OSError:
            print('Error al generar los directorios necesarios, asegurese de que el programa puede modificar directorios')
            return
    # Para abrir el fichero se hace esto:
    with open('tmp/user.json', 'w') as json_file:
        json.dump(user_log, json_file)

## read_user_log
#  Args:
#
#  Funcionalidad: devuelve la informacion del usuario actual
#  desde un fichero json
def read_user_log():
    # Para abrir el fichero se hace esto:
    with open('tmp/user.json') as json_file:
    	return json.load(json_file)

## write_user_called
#  Args:
#  user_called: diccionario con la informacion del usuario
#
#  Funcionalidad: Guarda la informacion del usuario al que se llama
#  en un fichero json
def write_user_called(user_called):
    # Para abrir el fichero se hace esto:
    with open('tmp/user_called.json', 'w') as json_file:
        json.dump(user_called, json_file)

## read_user_called
#  Args:
#
#  Funcionalidad: devuelve la informacion del usuario al que se llama
#  desde un fichero json
def read_user_called():
    # Para abrir el fichero se hace esto:
    with open('tmp/user_called.json') as json_file:
        return json.load(json_file)