import socket
import threading
import re
import math

mutex = threading.Lock()

# Socket para conectarse con el servidor
SERVER_HOST = "54.172.181.206"
SERVER_PORT = 10070 # y su puerto
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Se crea diccionario que redirecciona a los usuarios a la web que se desean conectar
web_page_dict = {}
web_page_dict['10081'] = ("www.internetworking.cl", 80)
web_page_dict['10082'] = ("www.el4203.ml", 80)
web_page_dict['10083'] = ("www.el4203.ml", 5000)
web_page_dict['10084'] = ("192.168.100.172", 80)

# Se conecta al servidor
print(f"[*] Conectando con el servidor {SERVER_HOST}:{SERVER_PORT}...")
s.connect((SERVER_HOST, SERVER_PORT))
print("[+] Conectado.")

# Función que se comunica al cliente con la web deseada
def web_client(user_request):

    # Se separa el mansaje recibido en sus partes
    separate_full = re.split(b'<SEP>',user_request)
    ip_user = separate_full[0]
    port_user = separate_full[1]
    puerto_encontrado = separate_full[2].decode()
    web_request = separate_full[3]

    # Se abre un socket para enviar la solicitud a la web
    web_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    web_page, port_web_page = web_page_dict[puerto_encontrado]
    web_socket.connect((web_page, port_web_page))

    # Se envía la solicitud a la web
    with mutex:
        web_socket.sendall(web_request)

    # Se recibe la respuesta de la web (por partes)
    response = b''
    web_socket.settimeout(0.5)
    try: 
        while True:
            chunk = web_socket.recv(8192)
            if len(chunk) == 0:     
                break
            response = response + chunk
    except socket.timeout as e:
        pass

    # La respuesta recibida se divide en paquetes de largo fijo
    largo_paquete = 8192-36
    cantidad_paquetes = str(math.ceil(len(response)/largo_paquete))

    # Se preparan la etiqueta para la cantidad de paquetes
    while len(cantidad_paquetes)<5:
        cantidad_paquetes='0'+cantidad_paquetes

    # Si se recibe una respuesta vacia se le agregan las etiquetas y se envia al servidor
    if response == b'':
        partial = (ip_user + b'<SEP>' + port_user + b'<SEP>' b'00001' +  b'<SEP>' + b'00001' + b'<SEP>' + b'matalo')
        partial = partial + b'#'*(8192-len(partial))
        with mutex:
            s.sendall(partial)

    # Si la respuesta no es vacía, se envía en paquetes de largo fijo
    else:
        for n in range(1, int(cantidad_paquetes)+1):

            # Si es el ultimo paquete se procesa para lograr el largo fijo (se rellena con #) y se envía al servidor
            if n == int(cantidad_paquetes):
                partial = (ip_user + b'<SEP>' + port_user + b'<SEP>' + cantidad_paquetes.encode() +  b'<SEP>' +cantidad_paquetes.encode() + b'<SEP>' + response[(n-1)*largo_paquete:])
                partial = partial + b'#'*(8192-len(partial))
                with mutex:
                    s.sendall(partial)

            else:
                # Revisa cuantos ceros debe añadir segun el numero actual de paquete para que el paquete tenga un largo fijo y se envía al servidor
                paquete_actual_ceros = b'0'*(5-len(str(n))) + str(n).encode()
                with mutex:
                    s.sendall(ip_user + b'<SEP>' + port_user  + b'<SEP>' + paquete_actual_ceros +  b'<SEP>' +cantidad_paquetes.encode() + b'<SEP>' + response[(n-1)*largo_paquete:n*largo_paquete])
    
    # Se cierra el socket creado para la solicitud
    web_socket.close()
    return

# Lo primero que realiza el cliente es autenicarse
inicio_autenticacion = s.recv(4096)
print(inicio_autenticacion.decode())   


while True: 
    # Se envía la clave al servidor
    clave = input("Ingrese su clave de cliente: ")
    s.sendall(clave.encode())

    respuesta_autenticacion = s.recv(4096)

    if respuesta_autenticacion.decode() == "OK":
        # Si es la clave correcta, se espera a la conexión de usuarios
        print("Contraseña valida, esperando solicitudes")
        while True:
            
            data_recv = s.recv(8196)

            # Cuando se recibe una solicitud se abre un hilo para comunicarse con la web
            if data_recv != b'':
                client_thread = threading.Thread(target=web_client, args=(data_recv,))
                client_thread.daemon = True
                client_thread.start()

    else:
        # Si la contraseña es incorrecta se vuelve a pedir
        print(respuesta_autenticacion.decode())