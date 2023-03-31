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
import socket
import sys, getopt
import functools

sys.path.append('.')

import os
import pqcrypto
import time
import requests
import datetime
import math
import operator
import FaBo9Axis_MPU9250
import os.path

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from secrets import compare_digest
#from pqcrypto.kem.kyber768 import generate_keypair, encrypt, decrypt
from pqcrypto.sign.dilithium2 import generate_keypair, sign, verify
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes



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
    j=0


    print('waiting for a connection')
    client_sock, client_info = server_sock.accept()
    print("Accepted connection from ", client_info)

    mpu9250 = FaBo9Axis_MPU9250.MPU9250()

    while True:
        tiempo=datetime.datetime.now()
        accel = mpu9250.readAccel()
        magnitud = math.sqrt(((accel['x'])**2)+((accel['y'])**2)+((accel['z'])**2))
        gyro = mpu9250.readGyro()
        magnitudG = math.sqrt(((gyro['x'])**2)+((gyro['y'])**2)+((gyro['z'])**2))

        if j==0:
            f=open('nuevo.txt','w')
            f.write(str(magnitudG) + '\n' + str(magnitud))
            f.close
            j=j+1

        else:
            f=open('nuevo.txt','a')
            f.write('\n' + str(magnitudG) + '\n')
            f.write(str(magnitud))
            f.close

            j= j+1
        time.sleep(0.01)
        if j==200: break
    start_time = time.time()
    j=0
    f=open('nuevo.txt','r')
    read_file=f.readlines()
    f.close
    pos=0
    pos1=1
    aux=0
    n = 0
    m = 90
    pos=1
    apuntador = 0
    apuntado = 1
    ### obteniendo valor para covarianza de vectores
    while  True:
      for i in range (1,100):
          magnitud_t = magnitud_t + float(read_file[pos])
          magnitudG_t = magnitudG_t + float(read_file[n])
          n=n+2
          pos=pos+2
          #print(n)
      med=magnitud_t/100
      medG = magnitudG_t/100
      sumdes=0.0
      sumdesG=0.0
      n = 0
      pos = 1
      for i in range (1,100):
          sumdes= sumdes + (float(read_file[pos])-med)**2
          sumdesG= sumdesG + (float(read_file[n])-med)**2
          n=n+2
          pos=pos+2
      des = math.sqrt(sumdes/100)
      desG = math.sqrt(sumdesG/100)
      aux = 0.0
      auxG = 0.0
      pos=1
      n=0
      for i in range(1,100):
          aux = aux + ((float(read_file[pos])-med)/des)
          auxG = auxG + ((float(read_file[pos])-medG)/desG)
          n=n+2
          pos=pos+2

      cov = aux/99
      covG = auxG/99
      if m == 140:
          #print(m)
          break
      if apuntador == 0:
          f=open('giroscopio.txt','w')
          f.write(str(covG) + '\n')
          f.close
          f=open('acelerometro.txt','w')
          f.write(str(cov) + '\n')
          f.close
          magnitudG_t = 0.0
          magnitud_t = 0.0
          apuntador = apuntador + 2
          apuntado = apuntado + 2
          n=apuntador
          pos=apuntado
      else:
          f=open('giroscopio.txt','a')
          f.write(str(covG) + '\n')
          f.close
          f=open('acelerometro.txt','a')
          f.write(str(cov) + '\n')
          f.close
          magnitudG_t = 0.0
          magnitud_t = 0.0
          apuntador = apuntador + 2
          apuntado = apuntado + 2
          n=apuntador
          pos=apuntado
      m=m+1
    try:
        f=open('acc_ext.txt','w')
        f.write("")
        f.close()
        f=open('giro_ext.txt','w')
        f.write("")
        f.close()

        CHUNK_SIZE = 1024
        len_chunk = CHUNK_SIZE
        with open('conexion1.txt', "wb") as f:
            chunk = client_sock.recv(CHUNK_SIZE)
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
        #server_sock.close()

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
    f=open('conexion1.txt','r')
    read_file=f.readlines()
    f.close
    pos=0
    pos1=1
    for i in range(0,49):

        f=open('giro_ext.txt','a')
        f.write(read_file[pos])
        f.close
        pos=pos+2
        f=open('acc_ext.txt','a')
        f.write(read_file[pos1])
        f.close
        pos1=pos1+2
        #j=j+1
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
    cov=0.0
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
    covG=0.0
    f=open('giroscopio.txt','r')
    read_file = f.readlines()
    f.close
    g=open('giro_ext.txt', 'r')
    read_files = g.readlines()
    g.close
    f=open('acelerometro.txt','r')
    read_fil = f.readlines()
    g=open('acc_ext.txt', 'r')
    read_fils = g.readlines()
    g.close
    pos=0
    pos1=0
    tiempo=datetime.datetime.now()
       #####covarianza y fusion
    f=open('resultados.txt','a')
    f.write(str(tiempo) + '\n')
    g = open('ayuda.txt', 'a')

    for i in range(1,50):

        auxiliar= ((float(read_fil[pos]))*(float(read_fils[pos])))
        pos=pos+1
        auxiliarG= ((float(read_file[pos1]))*(float(read_files[pos1])))
        pos1=pos1+1
        cov = auxiliar
        covG = auxiliarG
        fusion=0.0
        if cov >= 0.2:
            fusion = cov
        else:
            fusion=(cov+covG)/2
        print ('F = %f', fusion)
        f.write(str(fusion) + '\n')
        g.write(str(fusion) + '\n')
        suma = suma + fusion
    f.close()
    g.close()

    media = suma/50
    f = open('ayuda.txt','r')
    read = f.readlines()
    f.close()
    for i in range (0,49):
        ayuda = ayuda + ((float(read[i]) - media )**2)
    d_e = math.sqrt(ayuda/49)

    t = (media - 0.2)/(math.sqrt(d_e/50))
    if t>= 1.296:
        print ("sensor aceptado")
        confirmacion = b'1'
        client_sock.send(confirmacion)
        id_sensor = client_sock.recv(1024)

    else:
        print ("sensor rechazado")
        id_sensor = b' '


    elapsed_time = time.time() - start_time
    print("tiempo de ejecucion: %.10f segundos." %elapsed_time)

    return id_sensor



'''
Nombre:     encriptar

Descripcion: encripta cualquier tipo de arcvhivo y regresa un archivo .enc

Argumentos      --dire: Direccion donde se encuentra el archivo a ecriptar
                --key: llave con la que se desea encriptar el archivo
                --iv: vector iv que se utilizo en la encriptacion
                --dirout: direccion del archivo de salida .enc que se obtendra
'''

def encriptar(dire, key, iv, dirout):
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


'''
Nombre:     desencriptar

Descripcion: Desencripta un arcvhivo .enc en el original, se debe agregar la terminacion del archivo que se desea recuperar
             Ejemplo: Si el archivo original es un txt, se debe ingresar un archivo a la direccion de salida del mismo tipo txt.

Argumentos      --dire: Direccion donde se encuentra el archivo .enc
                --key: llave con la que se encripto el archivo
                --iv: vector iv que se utilizo en la encriptacion
                --dirout: direccion del archivo de salida que se dese obtener
'''

def desencriptar(dire, key, iv, dirout):
    archivo = open(dire, "rb")
    tam = os.path.getsize(dire)
    encriptador = AES.new(key, AES.MODE_CBC, iv)
    archivo_desencriptado = open(dirout, 'wb')
    while True:
        data = archivo.read(256)
        #print(data)
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


'''
Nombre encapsulado

Descripcion: Encapsula con Kyber obteniendo el Ct con la public key recibida desde el servidor,

Argumentos:     --id ingresa el ID del cliente

Returns:        --regresa la llave generada despues de pasarla por un KDF
                --regresa los primeros 16 digitos del hasheo generado a traves del ID y el ct

'''


def encapsulado(id):
    #Importamos la libreria de kyber
    from pqcrypto.kem.kyber512 import generate_keypair, encrypt, decrypt
    #recibimos la public key
    public_key = sock.recv(800)
    #Se realiza el encapsulado y se obtenemos el CT y el PT
    ciphertext, plaintext_original = encrypt(public_key)
    #Enviamos el CT
    sock.sendall(ciphertext)
    #Concatenamos el CT con el ID del cliente
    ct_hash = ciphertext + id
    #Realizamos el hash al CT con el ID
    hash = SHA256.new()
    hash.update(ct_hash)
    ct_hash = hash.digest()
    #Enviamos el hash
    sock.sendall(ct_hash)
    #data = sock.recv(1024)
    #print(len(data))
    #print(compare_digest(plaintext_original, data))
    #time.sleep(1)
    #salt = b'1234567891123456'
    #con una funcion KDF se obtiene una llave a traves del PT y el hash
    key = scrypt(plaintext_original, ct_hash, 16, N=2**14, r=8, p=1)
    return key, ct_hash[0:16]

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port on the server
# given by the caller
#este socket es para utilizar con el Servidor
HOST=sys.argv[1]
PORT=5001
server_address = (HOST, PORT)
#print('connecting to {} port {}'.format(*server_address))
#sock.connect(server_address)

#se declara un segundo socket para la autenticacion de sensores
#WARNING: la direccion debe ser diferente al anterior socket
start_time = time.time()
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST_SOCK = sys.argv[2]
PORT_SOCK = 5005
server_sock_address = (HOST_SOCK, PORT_SOCK)
server_sock.bind(server_sock_address)
server_sock.listen(1)

#declaramos rutas a utilizar
route_in = 'resultados.txt'
route_out = 'doc_enc.enc'
route_out2 = 'doc_dec_2.txt'
CHUNK_SIZE = 1024
#declaramos IDs
id_b =b'12.34.56.78'
id_d = b'87.65.43.21'
ip_c = '192.168.100.59'

try:
    #FASE 0
    id_sensor = corre_imu(server_sock)
    print("El ID del sensor es:")
    print(id_sensor)

    #FASE1
    print('connecting to {} port {}'.format(*server_address))
    sock.connect(server_address)

    amount_expected = 1184
    amount_received = 0
    key , iv= encapsulado(id_b)
    #FINFASE1

    #FASE2
    #Recibimos la Pk para la firma
    public_key_sign=sock.recv(1184)
    #Encriptamos el archivo a enviar
    encriptar(route_in,key,iv,route_out)

    #Enviamos el archivo

    tam_doc = os.path.getsize(route_out)
    print(tam_doc)

    #confirmacion = True
    #while confirmacion:
    with open(route_out, 'rb') as f:
        data = f.read(CHUNK_SIZE)
        while data:
            print("sending...")
            time.sleep(.5)
            sock.send(data)
            data = f.read(CHUNK_SIZE)
        #sock.sendfile(f,0,tam_doc)
        #print('documento enviado')
    f.close()
     #   lon_rec = sock.recv(len(tam_doc))
      #  sock.send(tam_doc)
      #  print("Longitudes ")
      #  print(lon_rec)
       # print(tam_doc)
       # confirmacion = compare_digest(lon_rec,tam_doc)

    #Leemos el mensaje del archivo
    f = open(route_out, 'rb')
    mensaje = f.read()
    f.close()

    #recibimos el mensaje unico
    mi = sock.recv(32)
    print(mi)
    #recibimos el mensaje hasheado
    msg_hash = sock.recv(32)
    print(msg_hash)
    #recibimos el bloque de firma
    signature2 = sock.recv(1024)
    signature3 = sock.recv(1024)
    signature = signature2 + signature3
    print(len(signature2))
    print(len(signature3))
    print(len(signature))

    msg_hash_esperado = id_d + signature + mi + mensaje
    #print(msg_hash_esperado)
    hash = SHA256.new()
    hash.update(msg_hash_esperado)
    msg_hash_esperado = hash.digest()

    #print(msg_hash_esperado)
    #verificamos que el hasheo que recibimos sea el mismo
    print("Verificacion de HMIm =")
    print(compare_digest(msg_hash_esperado,msg_hash))
    #verificamos quie la firma sea autentica
    print("Verificacion de bloque de firma = ")
    print(verify(public_key_sign,mi,signature))
    #FINFASE2

    #INICIOFASE3
    #concatenamos el idd con mi
    msg_hash_mi=id_d+mi
    #hasheamso el mensaje concatenado
    hash = SHA256.new()
    hash.update(msg_hash_mi)
    msg_hash_mi = hash.digest()
    #adjuntamos los datos que mandaremos al arduino
    data = {'mi':mi,'hash_mi':msg_hash_mi}
    #
    direccion = 'http://192.168.100.59/hash'
    #hacemos una peticioon para que el arduino haga la validacion
    requests.post(direccion,data)
    #FINFASE3

finally:
    sock.close()
