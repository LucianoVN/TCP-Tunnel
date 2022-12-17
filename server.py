# Se importan librerías necesarias
import socket
import re
import threading
import sys
import datetime
import utils # librería con funciones y clases complementarias

# Se define el número de recursiones para no tener problemas en la ejecución
sys.setrecursionlimit(10000)

# Socket para conectar con el cliente
HOST = "0.0.0.0"  
Client_PORT = 10070
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Clace de autenticación del cliente
clave_cliente = '1234'

# Se definen los puertos donde se recibirán solicitudes de los usuarios
puertos_disponibles_usuarios= [10081,10082,10083,10084]

# Lista con los sockets que levanta el usuario
sock_usuarios = []

# Lista con los mensajes que está procesando el servidor
mensajes = []

# Diccionario con mapeo de ip usuario -> id
mapeo_ip = {}
conteo_ip = 0 

# Configurarción del mutex para trabajar con múltiples hilos
mutex = threading.Lock()

# Función que retorna la llave de un valor
def get_key(val):
    for key, value in mapeo_ip.items():
        if val == value:
            return key


# Lista con usuarios conectados para crear interfaz
lista_conectados = []

recibiendo_usuarios = False # Variable definida para actualizar la interfaz de forma conveniente

# Función que actualiza una interfaz con la información de las conexiones
def actualiza_interfaz():
    # Tabla base para desplegar la informacion
    tabla_conectados = {'10081': ["www.internetworking.cl:80", 0, ''],
                        '10082': ["www.el4203.ml:80", 0, ''],
                        '10083': ["www.el4203.ml:5000", 0, ''],
                        '10084': ["192.168.100.172:80", 0, '']}

    # Se agrega la información a la tabla
    for conexion in lista_conectados:
        tabla_conectados[str(conexion[1])][1] += 1
        tabla_conectados[str(conexion[1])][2] = tabla_conectados[str(conexion[1])][2] + ' '+ conexion[0].decode()
    
    global recibiendo_usuarios

    # Cuando se actualiza, se elimina la tabla desplegada anteriormente
    if recibiendo_usuarios:
        utils.delete_last_line()
        utils.delete_last_line()
        utils.delete_last_line()
        utils.delete_last_line()
        utils.delete_last_line()
        utils.delete_last_line()
        utils.delete_last_line()
        utils.delete_last_line()

    # Se imprime la interfaz con el formato deseado
    print('-----------------------------------------------------------')
    print('[{0:s}] Última Actualización: {1:s}'.format('*', datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')))
    print ("{:<30} {:<15} {:<10}".format('Web','# Conectados','IP conectadas'))
    for k,v in tabla_conectados.items():
        web, conteo, ip = v
        print ("{:<30} {:<15} {:<10}".format(web,conteo,ip))
    print('-----------------------------------------------------------')


# Función que abre un hilo para cada puerto por el cual se conectan los usuarios
def crear_puerto_usuario(port):

    # Se levantan los puertos para recibir las solicitudes de los usuarios
    HOST = "0.0.0.0"  
    User_PORT = port
    user_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    user_socket.bind((HOST, User_PORT))
    user_socket.listen()
    
    # Cuando se conecta un usuario, abre un hilo
    while True:
        user_conn, user_addr = user_socket.accept()
        user_thread = threading.Thread(target=usuario, args=(user_conn, user_addr, port))
        user_thread.daemon = True
        user_thread.start()

# Función que procesa los usuarios que se conectan al servidor
def usuario(user_conn, user_addr, port):

    # Se ingresan las variables globales a la función
    global sock_usuarios
    global mapeo_ip
    global conteo_ip    

    # Se guarda la información de la conexión del usuario
    user_port = str(user_addr[1]).encode()
    user_ip = user_addr[0].encode()
    webpage_port = str(port).encode()

    # Si a una web se conecta un nuevo usuario se actualiza la interfaz
    global lista_conectados
    with mutex:
        if (user_ip,port) not in lista_conectados:
                lista_conectados.append((user_ip,port))
                actualiza_interfaz()

    # Si es que el socket de un usuario no está en la lista de socket conectados, se agrega
    with mutex:
        if not (user_conn,user_addr) in sock_usuarios:
            sock_usuarios.append((user_conn,user_addr))
        else:
            print('--------------Intentando Agregar Socket Repetido-----------')
        
        # Se guarda el mapeo de la ip del usuario conectado en caso de no estar guardada
        if not user_ip.decode() in mapeo_ip.keys():
            mapeo_ip[user_ip.decode()] = str(conteo_ip)
            conteo_ip+=1

    # El servidor escucha las solicites del usuario y las procesa
    while True:
        
        # Se recibe la solicitud completa del usuario
        data = b''
        user_conn.settimeout(0.5)
        try: 
            while True:
                chunk = user_conn.recv(8192)
                if len(chunk) == 0: 
                    break
                data = data + chunk

        except socket.timeout as e:
            pass

        solicitud_recibida = False

        # Si se recibió una solicitud, se envía al cliente
        if data != b'':
            solicitud_recibida = True
            # Se le agregan los headers correspondientes al mensaje antes de enviarlo
            full_data = mapeo_ip[user_ip.decode()].encode() + b'<SEP>'+user_port +b'<SEP>'+ webpage_port + b'<SEP>'+ data
            with mutex:
                client_conn.sendall(full_data)
                
        # Cuando se recibe una solicitud, se queda esperando la respuesta del cliente
        if solicitud_recibida:
            # Variable que determina si la respuesta del cliente fue devuelta al usuario
            mensaje_devuelto=False

            # Se espera a recibir la respuesta del cliente
            while not mensaje_devuelto:
                # Se reciben los paquetes que envía el cliente
                with mutex:
                    client_response=b''
                    while True:
                        if len(client_response) == 0:
                            chunk = client_conn.recv(8192)
                            client_response = client_response + chunk
                        else: 
                            chunk = client_conn.recv(8192-len(client_response))
                            client_response = client_response + chunk
                        if len(client_response) == 8192:
                            break
                
                # Se procesa el paquete recibido separándolo en sus partes correspondientes
                separate_client_response = re.split(b'<SEP>',client_response)


                ip_client_response = separate_client_response[0]
                port_client_response = separate_client_response[1]
                paquete_actual = separate_client_response[2]
                paquetes_totales = separate_client_response[3]
                data_client_response = separate_client_response[4]

                # En caso de ser el último paquete de una respuesta se procesa de forma especial
                # para eliminar los elementos de relleno
                if int(paquete_actual.decode())==int(paquetes_totales.decode()):
                    if data_client_response[:6] == b'matalo':
                        data_client_response = b'matalo'
                    else:
                        data_raw = data_client_response
                        data_raw = data_raw[::-1]
                        while data_raw[0:1]==b'#':
                            data_raw=data_raw[1:]
                        data_raw = data_raw[::-1]
                        data_client_response = data_raw

                global mensajes
                completando_mensaje = False

                # Procesamiento especial cuando la respuesta a una solicitud son 0 bytes
                if data_client_response == b'matalo':
                    ip_recuperada = get_key(ip_client_response.decode())

                    # Se busca el socket correspondiente y se cierra la conexión
                    for sock in sock_usuarios:
                        if (ip_recuperada, int(port_client_response.decode()) ) == sock[1]:
                            # print(f"Encontré el socket, VOY A MATAR EL SOCKET {ip_client_response.decode()}, {port_client_response.decode()}")
                            sock[0].close()
                            with mutex:
                                sock_usuarios.remove(sock)
                            return

                # Si es que se recibe una respuesta desde la pagina web se guardan los paquetes
                else:
                    # Se analiza si el paquete recibido es parte de un mensaje que es está completando 
                    for mensaje in mensajes:
                        if mensaje['ID']==(ip_client_response.decode(), port_client_response.decode()):
                            completando_mensaje = True
                            with mutex:
                                mensaje['Data'].append((int(paquete_actual.decode()),data_client_response))
                                mensaje['Actuales'] += 1

                            # Si el mensaje está completo se procede a reconstruirlo
                            if mensaje['Actuales']==int(paquetes_totales.decode()):

                                # Se reconstruye el mensaje ordenandolo mediante un arbol de búsqueda binaria
                                respuesta_reconstruida = utils.ordena_ABB(mensaje['Data'])

                                ip_recuperada = get_key(ip_client_response.decode())
                                for sock in sock_usuarios:
                                    if (ip_recuperada, int(port_client_response.decode()) ) == sock[1]:
                                        
                                        with mutex:
                                            sock[0].settimeout(None)
                                            sock[0].sendall(respuesta_reconstruida)
                                            sock[0].settimeout(0.5)
                                            mensajes.remove(mensaje)
                                        mensaje_devuelto = True
                                        break
                            break
                    
                    # Si no pertenece a ningún mensaje, se agrega o se envía si es de largo 1
                    if not completando_mensaje:
                        # Si la respuesta es un único paquete se envía al usuario
                        if int(paquetes_totales.decode())==1:
                            ip_recuperada = get_key(ip_client_response.decode())
                            for sock in sock_usuarios:
                                if (ip_recuperada, int(port_client_response.decode()) ) == sock[1]:
                                    
                                    with mutex:   
                                        sock[0].settimeout(None)
                                        sock[0].sendall(data_client_response)
                                        sock[0].settimeout(0.5)
                                        mensaje_devuelto = True
                                    break
                        # Si la respuesta es más de un paquete se guarda y se esperan los siguientes
                        else: 
                            with mutex:
                                mensajes.append({'ID':(ip_client_response.decode(), port_client_response.decode()), 'Data': [(int(paquete_actual.decode()),data_client_response)], 'Actuales':1})
                  
try:
    # Se inicializa el socket para el cliente
    client_socket.bind((HOST, Client_PORT))
    client_socket.listen()
    print(f"[*] Servidor escuchando cliente en {HOST}: {Client_PORT}")
    client_conn, client_addr = client_socket.accept()

    # Cuando hay un cliente conectado, se procede a autenticar
    with client_conn:
        print(f"[*] Se recibió una conexión de un cliente en: {client_addr}")
        client_conn.send('Conexión recibida, por favor autenticar.'.encode())

        autenticando = True
        while autenticando:
            # Se recibe la clave ingresada
            intento_clave = client_conn.recv(4096)
            if intento_clave.decode() == clave_cliente:
                # Si es la clave correcta se para de autenticar
                print(f"[*] Cliente autenticado correctamente en: {client_addr}. Se esperan conexiones de usuarios.")
                client_conn.send('OK'.encode())
                autenticando = False

            else:
                # Si es la clave incorrecta se pide ingresarla nuevamente
                client_conn.send('Clave inválida, intente nuevamente.'.encode())

        # Se imprime la interfaz para ver el estado de las conexiones
        actualiza_interfaz()
        recibiendo_usuarios = True

        # Cuando se autentica un cliente, se abren los puertos para recibir las solicitudes de los clientes
        # Cada puerto se ejecuta en un hilo distinto para recibir solicitudes en simultáneo
        for puerto in puertos_disponibles_usuarios:
            user_thread = threading.Thread(target=crear_puerto_usuario, args=(puerto,))
            user_thread.daemon = True
            user_thread.start()
        user_thread.join()

except KeyboardInterrupt:
    print('KeyboardInterruption')

# Cuando se deja de ejcutar el servidor se cierran los puertos
finally:
    client_socket.close()