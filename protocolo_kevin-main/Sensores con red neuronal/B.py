'''
Para correr el siguiente programa debe usarse versiones posteriores a python 3
y al llamarse debe incluirse dos argurmentos, el primer argumento es la
direccion IP a la que desea conectarse el nodo coordinador, en otras palabras la
direccion IP del servidor A. El segundo argumento es la direccion con la que
cuenta el nodo coordinador

Ejemplo:
"python3 server.py 192.168.100.11 192.168.100.90"

El siguiente programa sera corrido en el Nodo Coordinador B
Se deben descargar las bibliotecas pycryptodome, pqcrypto y FaBo9Axis_MPU9250
'''
import pickle
import socket
import sys
from enum import Enum

import psutil
import os
import datetime
import math
import FaBo9Axis_MPU9250
import os.path
import time
import numpy as np
import keras.models
import requests
import csv
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from secrets import compare_digest
from pqcrypto.sign.dilithium2 import verify
from Crypto.Protocol.KDF import scrypt

sys.path.append('.')


class Stage(Enum):
    INICIAL = 0
    FASE_0 = 1
    FASE_1 = 2
    FASE_2 = 3
    FASE_3 = 4
    FASE_4 = 5


class StatTracker:
    output_file_template = 'StatResults{0}.{1}'
    estimated_cpu_cycles = 0
    previous_timer = 0
    delay = 0
    number_of_delays = 0
    header_spacer = [None] * 2
    csv_header1 = (["Inicial"] + header_spacer + ["Fase 0"] + header_spacer + ["Fase 1"] + header_spacer
                   + ["Fase 2"] + header_spacer + ["Fase 3"] + header_spacer + ["Fase 4"] + header_spacer)
    csv_header2 = ["Memoria usada (MB)", "Tiempo (s)", "Ciclos de reloj estimados"]

    def reset_clock(self):
        self.previous_timer = self.initialization_time = time.perf_counter()
        self.final_time = 0

    def set_stats(self, stage: Stage):
        # Se usa perf_counter al ser de precision, es el timer default usado por timeit
        # No se usa timeit en esta clase dado que será una medición única y con tareas bloqueantes
        if stage == Stage.FASE_0:
            self.number_of_delays = 150
            self.delay = 0.01
        if stage == Stage.FASE_2:
            self.delay = 0.5
        self.final_time -= (self.delay * self.number_of_delays)
        self.elapsed_time = time.perf_counter() - self.previous_timer - (self.delay * self.number_of_delays)
        self.estimated_cpu_cycles = psutil.cpu_freq().current * self.elapsed_time * 10e6
        self.used_mem: int = self.total_memory - psutil.virtual_memory().available
        if stage == Stage.FASE_4:
            self.final_time += time.perf_counter() - self.initialization_time
        self.number_of_delays = 0
        print(f"Tiempo {stage.name}\n" + str(time.perf_counter() - self.previous_timer))
        option = ""
        # while option.strip().lower() != "y":
        #     option = input("Continuar? [y/n]")
        #     if option.strip().lower() != "n" and option.strip().lower() != "y":
        #         option = input("Seleccionar [y/n]")
        # self.previous_timer = time.perf_counter()

    def write_stats(self, stage: Stage):
        self.set_stats(stage)
        if self.csv_file:
            with open(self.output_file, 'a') as file:
                file.write(
                    str(self.used_mem / 1024) + ','
                    + str(self.elapsed_time) + ','
                    + str(self.estimated_cpu_cycles)
                    + ',')
                if stage == Stage.FASE_4:
                    file.write(str(self.final_time) + '\n')

        else:
            with open(self.output_file, 'a') as file:
                file.write("Uso de memoria {0}\n".format(stage.name))
                file.write(str(self.used_mem / 1024) + " MB\n")
                file.write("Tiempo transcurrido {0} (s)\n".format(stage.name))
                file.write(str(self.elapsed_time) + "\n")
                file.write("Ciclos de reloj estimados {0}\n".format(stage.name))
                file.write(str(self.estimated_cpu_cycles) + "\n")

    def __init__(self, csv_file=False):
        self.final_time = None
        self.total_memory = psutil.virtual_memory().total
        self.used_mem = self.total_memory - psutil.virtual_memory().available
        self.initialization_time = time.perf_counter()
        self.elapsed_time = 0
        self.csv_file = csv_file
        now = datetime.datetime.now()
        if csv_file:
            self.output_file = self.output_file_template.format(now.strftime(f"%d %m %Y"), "csv")
            with open(self.output_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(self.csv_header1)
                writer.writerow(self.csv_header2 * 6 + ["Tiempo total"])
        else:
            self.output_file = self.output_file_template.format(now.strftime(f"%d %m %Y %H:%M:%S"), "txt")
            with open(self.output_file, 'w') as file:
                f.write("Estadísticas del {0}".format(now.strftime(f"%d %m %Y %H:%M:%S")) + "\n")
        # self.write_stats(Stage.INICIAL)


def obtener_datos_B():
    dato = [[], [], [], [], [], []]
    mpu9250 = FaBo9Axis_MPU9250.MPU9250()
    for j in range(150):
        accel = mpu9250.readAccel()
        gyro = mpu9250.readGyro()
        # accel = {'x': random.triangular(-10, 10, 0), 'y': random.triangular(-10, 10, 0),
        #          'z': random.triangular(-10, 10, 0)}
        # gyro = {'x': random.triangular(-10, 10, 0), 'y': random.triangular(-10, 10, 0),
        #         'z': random.triangular(-10, 10, 0)}
        datos = [accel['x'], accel['y'], accel['y'], gyro['x'], gyro['y'], gyro['z']]
        for a, d in enumerate(datos):
            dato[a].append(d)
        time.sleep(0.01)
    return dato


def obtener_datos_C(client_sock):
    data_block = b''
    while True:
        # data = client_sock.recv(4096)
        # if not data: break
        # data = client_sock.recv(8140, socket.MSG_WAITALL)
        chunk = client_sock.recv(CHUNK_SIZE)
        data_block += chunk
        if len(chunk) < CHUNK_SIZE:
            break

    data_arr = pickle.loads(data_block)
    return data_arr


def comparacion_nn(client_sock, model):
    B = obtener_datos_B()
    C = obtener_datos_C(client_sock)
    print("Datos de B y C obtenidos")
    X = B + C
    X_t = np.array([np.array(X).T])
    print(np.shape(X_t))
    X = X_t.reshape((X_t.shape[0], 10, 1, 15, X_t.shape[2]))
    print(np.shape(X))
    pred = model.predict(X)
    print(pred[0])
    predicted_label = np.argmax(pred[0])
    # predicted_label = pred.argmax(axis=-1)
    print(predicted_label)
    if predicted_label == 0:
        resultado = 'Aceptado'
        confirmacion = b'1'
        client_sock.send(confirmacion)
        id_sensor = client_sock.recv(1024)
        with open(route_in, "w") as f:
            for element in (B + C):
                f.write(str(element))
    else:
        resultado = 'Rechazado'
        id_sensor = b' '
    print(resultado)
    return id_sensor


def run_imu(server_sock):
    '''
    run_imu

    Descripcion:    Lee datos del sensor y recibe los obtenidos del sensor externo
                    ademas de llamar a la funcion comparacion_nn()

    Argumentos:     --server_sock es la informacion del socket

    Returns:        --regresa el id del sensor

    '''
    print('Esperando conexión')
    client_sock, client_info = server_sock.accept()
    print("Conexión aceptada de ", client_info)
    model = keras.models.load_model('convlstm_sensors.h5')
    ID = comparacion_nn(client_sock, model)

    return ID


'''
Nombre corre_imu

Descripcion:    Lee datos del sensor y recibe los obtenidos del sensor externo
                ademas de llamar a la funcion comparacion()

Argumentos:     --server_sock es la informacion del socket

Returns:        --regresa el id del sensor

'''


def corre_imu(server_sock):
    magnitud = 0.0
    magnitudG = 0.0
    media = 0.0
    media_rec = 0.0
    d_e = 0.0
    suma = 0.0
    ayuda = 0.0
    magnitud_t = 0.0
    magnitudG_t = 0.0
    j = 0

    print('waiting for a connection')
    client_sock, client_info = server_sock.accept()
    print("Accepted connection from ", client_info)

    mpu9250 = FaBo9Axis_MPU9250.MPU9250()

    while True:
        tiempo = datetime.datetime.now()
        accel = mpu9250.readAccel()
        magnitud = math.sqrt(((accel['x']) ** 2) + ((accel['y']) ** 2) + ((accel['z']) ** 2))
        gyro = mpu9250.readGyro()
        magnitudG = math.sqrt(((gyro['x']) ** 2) + ((gyro['y']) ** 2) + ((gyro['z']) ** 2))

        if j == 0:
            f = open('nuevo.txt', 'w')
            f.write(str(magnitudG) + '\n' + str(magnitud))
            f.close
            j = j + 1

        else:
            f = open('nuevo.txt', 'a')
            f.write('\n' + str(magnitudG) + '\n')
            f.write(str(magnitud))
            f.close

            j = j + 1
        time.sleep(0.01)
        if j == 200: break
    start_time = time.time()
    j = 0
    f = open('nuevo.txt', 'r')
    read_file = f.readlines()
    f.close
    pos = 0
    pos1 = 1
    aux = 0
    n = 0
    m = 90
    pos = 1
    apuntador = 0
    apuntado = 1
    ### obteniendo valor para covarianza de vectores
    while True:
        for i in range(1, 100):
            magnitud_t = magnitud_t + float(read_file[pos])
            magnitudG_t = magnitudG_t + float(read_file[n])
            n = n + 2
            pos = pos + 2
            # print(n)
        med = magnitud_t / 100
        medG = magnitudG_t / 100
        sumdes = 0.0
        sumdesG = 0.0
        n = 0
        pos = 1
        for i in range(1, 100):
            sumdes = sumdes + (float(read_file[pos]) - med) ** 2
            sumdesG = sumdesG + (float(read_file[n]) - med) ** 2
            n = n + 2
            pos = pos + 2
        des = math.sqrt(sumdes / 100)
        desG = math.sqrt(sumdesG / 100)
        aux = 0.0
        auxG = 0.0
        pos = 1
        n = 0
        for i in range(1, 100):
            aux = aux + ((float(read_file[pos]) - med) / des)
            auxG = auxG + ((float(read_file[pos]) - medG) / desG)
            n = n + 2
            pos = pos + 2

        cov = aux / 99
        covG = auxG / 99
        if m == 140:
            # print(m)
            break
        if apuntador == 0:
            f = open('giroscopio.txt', 'w')
            f.write(str(covG) + '\n')
            f.close
            f = open('acelerometro.txt', 'w')
            f.write(str(cov) + '\n')
            f.close
            magnitudG_t = 0.0
            magnitud_t = 0.0
            apuntador = apuntador + 2
            apuntado = apuntado + 2
            n = apuntador
            pos = apuntado
        else:
            f = open('giroscopio.txt', 'a')
            f.write(str(covG) + '\n')
            f.close
            f = open('acelerometro.txt', 'a')
            f.write(str(cov) + '\n')
            f.close
            magnitudG_t = 0.0
            magnitud_t = 0.0
            apuntador = apuntador + 2
            apuntado = apuntado + 2
            n = apuntador
            pos = apuntado
        m = m + 1
    try:
        f = open('acc_ext.txt', 'w')
        f.write("")
        f.close()
        f = open('giro_ext.txt', 'w')
        f.write("")
        f.close()

        CHUNK_SIZE = 1024
        len_chunk = CHUNK_SIZE
        with open('conexion1.txt', "wb") as f:
            chunk = client_sock.recv(CHUNK_SIZE)
            len_chunk = len(chunk)
            while chunk:
                f.write(chunk)
                if len_chunk < CHUNK_SIZE:
                    break
                else:
                    chunk = client_sock.recv(CHUNK_SIZE)
                    len_chunk = len(chunk)
        f.close()

        id_sensor = comparacion(client_sock)

    except IOError:
        pass


    finally:
        client_sock.close()
        # server_sock.close()

    return id_sensor


'''
Nombre comparacion

Descripcion:    Realiza la comparacion de los datos obtenidos y recibidos para
                posteriormente identificar si pertenece a la red o no, ademas de
                enviarle una confirmacion al sensor de que pertenece a la red
                y posteriormente recibir su ID

Argumentos:     --client_sock es la informacion del socket del sensor

Returns:        --regresa el id del sensor

'''


def comparacion(client_sock):
    start_time = time.time()
    f = open('conexion1.txt', 'r')
    read_file = f.readlines()
    f.close
    pos = 0
    pos1 = 1
    for i in range(0, 49):
        f = open('giro_ext.txt', 'a')
        f.write(read_file[pos])
        f.close
        pos = pos + 2
        f = open('acc_ext.txt', 'a')
        f.write(read_file[pos1])
        f.close
        pos1 = pos1 + 2
        # j=j+1
    media = 0.0
    media_rec = 0.0
    d_e = 0.0
    d_e_r = 0.0
    suma = 0.0
    ayuda = 0.0
    ayuda_rec = 0.0
    j = 100
    suma_rec = 0.0
    auxiliar = 0.0
    cov = 0.0
    mediaG = 0.0
    media_recG = 0.0
    d_eG = 0.0
    d_e_rG = 0.0
    sumaG = 0.0
    ayudaG = 0.0
    ayuda_recG = 0.0
    j = 100
    suma_recG = 0.0
    auxiliarG = 0.0
    covG = 0.0
    f = open('giroscopio.txt', 'r')
    read_file = f.readlines()
    f.close
    g = open('giro_ext.txt', 'r')
    read_files = g.readlines()
    g.close
    f = open('acelerometro.txt', 'r')
    read_fil = f.readlines()
    g = open('acc_ext.txt', 'r')
    read_fils = g.readlines()
    g.close
    pos = 0
    pos1 = 0
    tiempo = datetime.datetime.now()
    #####covarianza y fusion
    f = open('resultados.txt', 'a')
    f.write(str(tiempo) + '\n')
    g = open('ayuda.txt', 'a')

    for i in range(1, 50):

        auxiliar = ((float(read_fil[pos])) * (float(read_fils[pos])))
        pos = pos + 1
        auxiliarG = ((float(read_file[pos1])) * (float(read_files[pos1])))
        pos1 = pos1 + 1
        cov = auxiliar
        covG = auxiliarG
        fusion = 0.0
        if cov >= 0.2:
            fusion = cov
        else:
            fusion = (cov + covG) / 2
        print('F = %f', fusion)
        f.write(str(fusion) + '\n')
        g.write(str(fusion) + '\n')
        suma = suma + fusion
    f.close()
    g.close()

    media = suma / 50
    f = open('ayuda.txt', 'r')
    read = f.readlines()
    f.close()
    for i in range(0, 49):
        ayuda = ayuda + ((float(read[i]) - media) ** 2)
    d_e = math.sqrt(ayuda / 49)

    t = (media - 0.2) / (math.sqrt(d_e / 50))
    if t >= 1.296:
        print("sensor aceptado")
        confirmacion = b'1'
        client_sock.send(confirmacion)
        id_sensor = client_sock.recv(1024)

    else:
        print("sensor rechazado")
        id_sensor = b' '

    elapsed_time = time.time() - start_time
    print("tiempo de ejecucion: %.10f segundos." % elapsed_time)

    return id_sensor


def encriptar(dire, key, iv, dirout):
    '''
    Nombre: encriptar

    Descripcion: encripta cualquier tipo de arcvhivo y regresa un archivo .enc

    Argumentos      --dire: Direccion donde se encuentra el archivo a ecriptar
                    --key: llave con la que se desea encriptar el archivo
                    --iv: vector iv que se utilizo en la encriptacion
                    --dirout: direccion del archivo de salida .enc que se obtendra
    '''
    encriptador = AES.new(key, AES.MODE_CBC, iv)
    archivo = open(dire, "rb")
    archivo_encriptado = open(dirout, "wb")
    while True:
        data = archivo.read(16)
        n = len(data)
        if n == 0:
            break
        elif n % 16 != 0:
            data += b' ' * (16 - n % 16)
        enc = encriptador.encrypt(data)
        archivo_encriptado.write(enc)
    archivo.close()
    archivo_encriptado.close()


def desencriptar(dire, key, iv, dirout):
    '''
    Nombre:     desencriptar

    Descripcion: Desencripta un arcvhivo .enc en el original, se debe agregar la terminacion del archivo que se desea recuperar
                 Ejemplo: Si el archivo original es un txt, se debe ingresar un archivo a la direccion de salida del mismo tipo txt.

    Argumentos      --dire: Direccion donde se encuentra el archivo .enc
                    --key: llave con la que se encripto el archivo
                    --iv: vector iv que se utilizo en la encriptacion
                    --dirout: direccion del archivo de salida que se dese obtener
    '''

    archivo = open(dire, "rb")
    tam = os.path.getsize(dire)
    encriptador = AES.new(key, AES.MODE_CBC, iv)
    archivo_desencriptado = open(dirout, 'wb')
    while True:
        data = archivo.read(256)
        n = len(data)
        if n == 0:
            break
        decd = encriptador.decrypt(data)
        n = len(decd)
        if tam > n:
            archivo_desencriptado.write(decd)
        else:
            archivo_desencriptado.write(decd[:tam])
        tam -= n
    archivo.close()
    archivo_desencriptado.close()


def encapsulado(id):
    '''
    Nombre encapsulado

    Descripcion: Encapsula con Kyber obteniendo el Ct con la public key recibida desde el servidor,

    Argumentos:     --id ingresa el ID del cliente

    Returns:        --regresa la llave generada despues de pasarla por un KDF
                    --regresa los primeros 16 digitos del hasheo generado a traves del ID y el ct

    '''

    # Importamos la libreria de kyber
    from pqcrypto.kem.kyber512 import encrypt
    # recibimos la public key
    public_key = sock.recv(800)
    # Se realiza el encapsulado y se obtenemos el CT y el PT
    ciphertext, plaintext_original = encrypt(public_key)
    # Enviamos el CT
    sock.sendall(ciphertext)
    # Concatenamos el CT con el ID del cliente
    ct_hash = ciphertext + id
    # Realizamos el hash al CT con el ID
    hash = SHA256.new()
    hash.update(ct_hash)
    ct_hash = hash.digest()
    # Enviamos el hash
    sock.sendall(ct_hash)
    # data = sock.recv(1024)
    # print(len(data))
    # print(compare_digest(plaintext_original, data))
    # time.sleep(1)
    # salt = b'1234567891123456'
    # con una funcion KDF se obtiene una llave a traves del PT y el hash
    key = scrypt(plaintext_original, ct_hash, 16, N=2 ** 14, r=8, p=1)
    return key, ct_hash[0:16]


# Connect the socket to the port on the server
# given by the caller
# este socket es para utilizar con el Servidor
HOST = sys.argv[1]
PORT = 5001
server_address = (HOST, PORT)
# print('connecting to {} port {}'.format(*server_address))
# sock.connect(server_address)

# se declara un segundo socket para la autenticacion de sensores
# WARNING: la direccion debe ser diferente al anterior socket
start_time = time.time()
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST_SOCK = sys.argv[2]
PORT_SOCK = 5005
server_sock_address = (HOST_SOCK, PORT_SOCK)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind(server_sock_address)
server_sock.listen(1)

# declaramos rutas a utilizar
route_in = 'resultados.txt'
route_out = 'doc_enc.enc'
route_out2 = 'doc_dec_2.txt'
CHUNK_SIZE = 1024
# declaramos IDs
id_b = b'12.34.56.78'
id_d = b'87.65.43.21'
ip_c = '192.168.100.59'

tracker = StatTracker(csv_file=True)
for i in range(2):
    # Create a TCP/IP socket
    tracker.reset_clock()
    tracker.write_stats(Stage.INICIAL)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # FASE 0
        # id_sensor = corre_imu(server_sock)

        id_sensor = run_imu(server_sock)
        print("El ID del sensor es:")
        print(id_sensor)
        tracker.write_stats(Stage.FASE_0)

        # FASE1

        print('connecting to {} port {}'.format(*server_address))
        sock.connect(server_address)

        amount_expected = 1184
        amount_received = 0
        key, iv = encapsulado(id_b)
        tracker.write_stats(Stage.FASE_1)

        # FINFASE1

        # FASE2

        # Recibimos la Pk para la firma
        public_key_sign = sock.recv(1184)
        # Encriptamos el archivo a enviar
        encriptar(route_in, key, iv, route_out)

        # Enviamos el archivo

        tam_doc = os.path.getsize(route_out)
        print(tam_doc)

        # confirmacion = True
        # while confirmacion:
        with open(route_out, 'rb') as f:
            data = f.read(CHUNK_SIZE)
            while data:
                tracker.number_of_delays += 1
                print("sending...")
                time.sleep(.5)
                sock.send(data)
                data = f.read(CHUNK_SIZE)
            # sock.sendfile(f,0,tam_doc)
            # print('documento enviado')
        f.close()
        #   lon_rec = sock.recv(len(tam_doc))
        #  sock.send(tam_doc)
        #  print("Longitudes ")
        #  print(lon_rec)
        # print(tam_doc)
        # confirmacion = compare_digest(lon_rec,tam_doc)
        tracker.write_stats(Stage.FASE_2)
        # FIN FASE 2 ACTUALIZADA

        # Leemos el mensaje del archivo
        # INICIO FASE 3 ACTUALIZADA

        f = open(route_out, 'rb')
        mensaje = f.read()
        f.close()

        # recibimos el mensaje unico
        mi = sock.recv(32)
        print(mi)
        # recibimos el mensaje hasheado
        msg_hash = sock.recv(32)
        print(msg_hash)
        # recibimos el bloque de firma
        signature2 = sock.recv(1024)
        signature3 = sock.recv(1024)
        signature = signature2 + signature3
        print(len(signature2))
        print(len(signature3))
        print(len(signature))

        msg_hash_esperado = id_d + signature + mi + mensaje
        # print(msg_hash_esperado)
        hash = SHA256.new()
        hash.update(msg_hash_esperado)
        msg_hash_esperado = hash.digest()

        # print(msg_hash_esperado)
        # verificamos que el hasheo que recibimos sea el mismo
        print("Verificacion de HMIm =")
        print(compare_digest(msg_hash_esperado, msg_hash))
        # verificamos quie la firma sea autentica
        print("Verificacion de bloque de firma = ")
        print(verify(public_key_sign, mi, signature))

        tracker.write_stats(Stage.FASE_3)
        # FIN FASE 3 ACTUALIZADA

        # INICIO FASE 4 ACTUALIZADA

        # concatenamos el idd con mi
        msg_hash_mi = id_d + mi
        # hasheamso el mensaje concatenado
        hash = SHA256.new()
        hash.update(msg_hash_mi)
        msg_hash_mi = hash.digest()
        # adjuntamos los datos que mandaremos al arduino
        data = {'mi': mi, 'hash_mi': msg_hash_mi}
        #
        # hacemos una peticioon para que el arduino haga la validacion
        # direccion = 'http://192.168.100.59/hash'
        direccion = 'http://192.168.0.22/hash'
        requests.post(direccion, data)

        tracker.write_stats(Stage.FASE_4)
        # FIN FASE 4 ACTUALIZADA

    finally:
        sock.close()
