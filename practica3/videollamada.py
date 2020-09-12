import socket
import servidor_descubrimiento
import users_control
import cv2
from appJar import gui
from PIL import Image, ImageTk
import numpy as np 
import threading
import time

BUFF = 4096

## call
#  Args:
#  gui: referencia a la gui de la aplicacion
#  user_called: usuario al que se intenta llamar
#
#  Funcionalidad: Realiza una peticion de llamada,
#  si el receptor la acepta comienza a emitir video
#  y reproduce el video que emite el receptor
def call(gui, user_called):

    user_log = users_control.read_user_log()

    user_called_address = (user_called['ip'], int(user_called['port']))
    msg = 'CALLING ' + user_log['nick'] + ' ' + str(user_log['port'])
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if user_called['nick'] == user_log['nick']:
        gui.app.infoBox('Llamada denegada',
            'No te puedes llamar a ti mismo.')
        return None

    sock.connect(user_called_address)
    print(msg)
    sock.send(msg.encode())

    response = sock.recv(BUFF).decode()

    sock.close()

    response_split = response.split(' ')
    
    if response_split[0] == 'CALL_ACCEPTED':
        subVentana(gui)
        users_control.write_user_called(user_called)
        # inicio del envio y recepción de video
        captura = threading.Thread(target=capturaVideo, args=(gui, user_called_address),daemon=True)
        captura.start()
        reproduccion = threading.Thread(target=callProcess, args=(gui, user_called_address),daemon=True)
        reproduccion.start()


    elif response_split[0] == 'CALL_DENIED':
        gui.app.infoBox('Llamada denegada',
            'El usuario ' + user_called['nick'] + ' ha denegado la llamada.')
        return None
    elif response_split[0] == 'CALL_BUSY':
        gui.app.infoBox('Llamada denegada',
            'El usuario ' + user_called['nick'] + ' esta en otra llamada.')
        return None

    return None

## listen_call
#  Args:
#  gui: referencia a la gui de la aplicacion
#  sock: socket de espera de conexiones
#
#  Funcionalidad: Espera hasta recibir algun mensaje,
#  implementa las respuestas a los distintos mensajes
def listen_call(gui, sock):

    user_log = users_control.read_user_log()

    sock.listen(1)

    while 1 and users_control.on:
        conn, address = sock.accept()
        request = conn.recv(1024)

        request_split = request.decode().split(' ')
        

        if request_split[0] == 'CALLING':
            if not users_control.inCall:
                call_accepted = gui.app.yesNoBox('Llamada entrante', 'El usuario ' + request_split[1] + ' te esta llamando \n ¿Aceptar?')
                if call_accepted == False:
                    # No aceptamos la llamada
                    msg = 'CALL_DENIED ' + user_log['nick']
                    conn.sendall(msg.encode())

                else:
                    # Aceptamos la llamada
                    msg = 'CALL_ACCEPTED ' + user_log['nick'] + ' ' + user_log['port']
                    conn.sendall(msg.encode())
                    subVentana(gui)
                    user_call = servidor_descubrimiento.query(request_split[1])
                    users_control.write_user_called(user_call)

                    # inicio del envio y recepción de video (Igual que en el call)


                    user_called_address = (user_call['ip'], int(user_call['port']))
                    captura = threading.Thread(target=capturaVideo, args=(gui, user_called_address), daemon=True)
                    captura.start()
                    reproduccion = threading.Thread(target=callProcess, args=(gui, user_called_address),daemon=True)
                    reproduccion.start()
            else:
                msg = 'CALL_BUSY'
                conn.sendall(msg.encode())

        elif request_split[0] == 'CALL_HOLD':
            # Poner las cosas para que se pause el video de lo que queda por hacer
            users_control.hold=True
        elif request_split[0] == 'CALL_RESUME':
            # Poner las cosas para que se reanude el video de lo que queda por hacer

            users_control.hold =False
        elif request_split[0] == 'CALL_END':
            # Poner las cosas para que se acabe la llamada
            users_control.inCall=False
            gui.app.show()
            gui.app.hideSubWindow("Llamada en curso")

    
    conn.close()


## capturaVideo
#  Args:
#  gui: referencia a la gui de la aplicacion
#  user_called_address: usuario al que se intenta llamar
#
#  Funcionalidad: Retransmite al receptor las imagenes
#  captadas por la webcam
def capturaVideo(gui, user_called_address):
    
    sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        cap.open()

    # Capturamos un frame de la cámara o del vídeo
    while users_control.inCall and users_control.on:
        ret, frame = cap.read()
        frame = cv2.resize(frame, (400,300))
        encode_param = [cv2.IMWRITE_JPEG_QUALITY, 50]
        result, encimg = cv2.imencode('.jpg', frame, encode_param)
        encimg = encimg.tobytes()

        sock.sendto(encimg, user_called_address)
        while users_control.hold and users_control.on:
            time.sleep(0.001)
            
    sock.close()
## callProcess
#  Args:
#  gui: referencia a la gui de la aplicacion
#  a:
#
#  Funcionalidad: Reproduce el video transmitido
#  por el usuario con el que estamos en llamada
def callProcess(gui, a):
    user = users_control.read_user_log()
    sock2 = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock2.bind((user['ip'],int(user['port'])))        


    while users_control.inCall and users_control.on:
        data, addr = sock2.recvfrom(60000)
        decimg = cv2.imdecode(np.frombuffer(data,np.uint8), 1)

        frame = cv2.resize(decimg,(480,360))

        cv2_im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_tk = ImageTk.PhotoImage(image=Image.fromarray(cv2_im))

        # Lo mostramos en el gui
        gui.app.setImageData("video1", img_tk, fmt='PhotoImage')
        while users_control.hold and users_control.on:
            time.sleep(0.001)
    sock2.close()
## subventana
#  Args:
#  gui: referencia a la gui de la aplicacion
#
#  Funcionalidad: abre la ventana de llamada y pone
#  el flag de llamada a true
def subVentana(gui):

    users_control.inCall=True

    gui.app.hide()
    gui.app.showSubWindow("Llamada en curso")
    
## endCall
#  Args:
#  Funcionalidad: Envia el mensaje de finalizacion de llamada
def endCall():
    
    user = users_control.read_user_log()
    peer = users_control.read_user_called()
    
    msg = "CALL_END " + user['nick']

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = (peer['ip'],int(peer['port']))


    sock.connect(server_address)

    sock.send(msg.encode())
    sock.close()
## holdCall
#  Args:
#  Funcionalidad: Envia el mensaje de pausa de llamada
def holdCall():
    
    user = users_control.read_user_log()
    peer = users_control.read_user_called()
    
    msg = "CALL_HOLD " + user['nick']

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = (peer['ip'],int(peer['port']))


    sock.connect(server_address)

    sock.send(msg.encode())
    sock.close()
## resumeCall
#  Args:
#  Funcionalidad: Envia el mensaje de continuacion de llamada
def resumeCall():
    
    user = users_control.read_user_log()
    peer = users_control.read_user_called()
    
    msg = "CALL_RESUME " +user['nick']

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = (peer['ip'],int(peer['port']))


    sock.connect(server_address)

    sock.send(msg.encode())
    sock.close()