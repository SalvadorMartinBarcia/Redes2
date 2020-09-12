# import the library
from appJar import gui
from PIL import Image, ImageTk
import servidor_descubrimiento
import videollamada
import users_control
import cv2
import json
import os
import shutil
import threading
import socket

global sock

sock = None

class VideoClient(object):
	## callProcess
	#  Args:
	#  window_size: Tamaño de la ventana de la aplicación
	#
	#  Funcionalidad: Inicialización de la primera ventana
	def __init__(self, window_size):
		
		# Creamos una variable que contenga el GUI principal
		self.app = gui("Redes2 - P2P", window_size)
		self.app.setGuiPadding(10,10)


		# Etiquetas de entrada para el inicio de sesión
		self.app.addLabelEntry("Nombre de Usuario")
		self.app.addLabelEntry("Contraseña")


		#Sacamos la IP propia para ponerla como valor por defecto
		#https://www.tutorialspoint.com/python-program-to-find-the-ip-address-of-the-client
		hostname = socket.gethostname()
		ip_address = socket.gethostbyname(hostname)
		self.app.addLabelEntry("IP de escucha")
		self.app.setEntry("IP de escucha", ip_address)

		#Ponemos 8000 como el puerto por defecto
		self.app.addLabelEntry("Puerto de escucha")
		self.app.setEntry("Puerto de escucha", 8000)


		self.app.addButton("Iniciar Sesion", self.buttonsCallback)

		#Subventana para llamadas
		self.app.startSubWindow("Llamada en curso", modal = True)
		self.app.setSize(640, 520)
		#######Video#################
		self.app.addImage("video1", "imgs/webcam.gif")
		#############################
		self.app.addButtons(["Pausar", "Reanudar", "Colgar"], self.buttonsCallback)
		self.app.stopSubWindow()

	## homescreen
	#  Args:
	#
	#  Funcionalidad: Inicializar la ventana que 
	#  tiene toda la funcionalidad de la applicación
	def homescreen(self):
		user_log = users_control.read_user_log()
		# Quitamos las etiquetas del inicio de sesion
		self.app.hideButton("Iniciar Sesion")
		self.app.hideLabel("Nombre de Usuario")
		self.app.hideLabel("Contraseña")
		self.app.hideLabel("IP de escucha")
		self.app.hideLabel("Puerto de escucha")
		
		# Preparación del interfaz
		self.app.addLabel("title", "Cliente Multimedia P2P - Redes2 - " + user_log['nick'])

		self.app.addImage("video", "imgs/webcam.gif")

		# Añadir los botones
		self.app.addButtons(["Llamar", "Listar usuarios", "Buscar usuario", "Salir"], self.buttonsCallback)
		
		# Barra de estado
		# Debe actualizarse con información útil sobre la llamada (duración, FPS, etc...)
		# self.app.addStatusbar(fields=2)

	## start
	#  Args:
	#
	#  Funcionalidad: Empezar la aplicación
	def start(self):
		self.app.go()

	# Establece la resolución de la imagen capturada
	def setImageResolution(self, resolution):		
		# Se establece la resolución de captura de la webcam
		# Puede añadirse algún valor superior si la cámara lo permite
		# pero no modificar estos
		if resolution == "LOW":
			self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160) 
			self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120) 
		elif resolution == "MEDIUM":
			self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320) 
			self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240) 
		elif resolution == "HIGH":
			self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640) 
			self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) 
				
	# Función que gestiona los callbacks de los botones
	def buttonsCallback(self, button):
		global sock
		if button == "Salir":
			# Eliminamos el directorio temportal
			shutil.rmtree('tmp/')
			# Salimos de la aplicación
			users_control.on=False
			sock.close()
			self.app.stop()
		elif button == "Iniciar Sesion":
			# Inicia sesión con los datos introducidos
			nick = self.app.getEntry("Nombre de Usuario")
			password = self.app.getEntry("Contraseña")
			ip = self.app.getEntry("IP de escucha")
			port = self.app.getEntry("Puerto de escucha")

			control = servidor_descubrimiento.register(nick, password, ip, port)

			if control == "NOK":
				self.app.errorBox("Inicio de sesión", "Error al iniciar sesión")
			else:
				user_log = {}
				# rellenamos el diccionario con los datos del usuario logeado
				user_log = servidor_descubrimiento.query(nick)
				
				# Guardamos al usuario en un directorio para tenerlo siempre que lo necesitemos
				users_control.write_user_log(user_log)


				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

				user_logged_address = (user_log['ip'], int(user_log['port']))

				sock.bind(user_logged_address)


				# Iniciamos el hilo que espera llamadas en el puerto indicado
				listen_call_thread = threading.Thread(target = videollamada.listen_call,
										args = (self,sock), daemon = True)
				listen_call_thread.start()
				# llamamos a la pantalla principal
				self.homescreen()
		elif button == "Buscar usuario":
			nick = self.app.textBox("Buscar", 
				"Introduce el nick del usuario a buscar")
			if not nick:
				self.app.errorBox('Por favor introduce un usuario')
			else:		
				user_query = servidor_descubrimiento.query(nick)

				if not user_query:
					self.app.errorBox('No encontrado', 'El usuario ' + nick + ' no existe')
				else:
					msg = 'Nick: ' + user_query['nick'] + '\n'
					msg += 'IP: ' + user_query['ip'] + '\n'
					msg += 'Port: ' + user_query['port'] + '\n'
					msg += 'Protocol: ' + user_query['protocol']
					self.app.infoBox('Usuario encontrado', msg)
		elif button == "Listar usuarios":
			users = servidor_descubrimiento.list_users()
			self.app.infoBox('Usuarios', users)
		elif button == "Llamar":

			nick = self.app.textBox("Llamar", 
				"Introduce el nick del usuario a llamar")
			if nick:
				user_query = servidor_descubrimiento.query(nick)

				if not user_query:
					self.app.errorBox('No encontrado', 'El usuario ' + nick + ' no existe')
				else:
					videollamada.call(self, user_query)

		elif button == "Pausar":
			users_control.hold=True
			videollamada.holdCall()
		elif button == "Reanudar":
			users_control.hold=False
			videollamada.resumeCall()
		elif button == "Colgar":
			users_control.inCall=False
			self.app.hideSubWindow("Llamada en curso")
			self.app.show()
			videollamada.endCall()




if __name__ == '__main__':

	vc = VideoClient("640x520")

	# Crear aquí los threads de lectura, de recepción y,
	# en general, todo el código de inicialización que sea necesario
	# ...


	# Lanza el bucle principal del GUI
	# El control ya NO vuelve de esta función, por lo que todas las
	# acciones deberán ser gestionadas desde callbacks y threads
	vc.start()

