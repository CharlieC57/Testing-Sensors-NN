'''
Para corre el siguiente programa debe usarse versiones posteriores a python 3
y al llamarse debe incluirse un argurmento, dicho argumento es la direccion IP
dodne esta montado el servidorr.

Ejemplo:
"python3 server.py 192.168.100.11"

El siguiente programa sera corrido en el Servidor A
Se deben descargar las bibliotecas pycryptodome y pqcrypto
'''
import socket
import sys
import os
import pqcrypto
import time

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from secrets import compare_digest
from pqcrypto.sign.dilithium2 import generate_keypair, sign, verify
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes

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
    print(tam)
    while True:
        data = archivo.read(256)
        #print(data)
        n = len(data)
        if n == 0:
            break
        #print(n)
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
Nombre desencapsulado

Descripcion: Desencapsula el Ct obtenido desde del cliente, genera el par de llave con kyber y
realiza la validacion del hash creado co nel Ct y el ID del cliente

Argumentos:     --id ingresa el ID del cliente

Returns:        --regresa la llave generada despues de pasarla por un KDF
                --regresa los primeros 16 digitos del hasheo generado a traves del ID y el ct
'''
def desencapsulado(id):
    #declaramos la libreria de kyber
    from pqcrypto.kem.kyber512 import generate_keypair, encrypt, decrypt
    #generamos la llave publica y secreta
    public_key, secret_key = generate_keypair()
    #enviamos al cliente la llave publica
    connection.sendall(public_key)
    #recibimos el Ct del cliente
    ciphertext = connection.recv(768)
    #recibimos el hash generado en el cliente
    ct_hash = connection.recv(256)
    #Se concatena el Ct con el ID del cliente
    ct_hash_esperado = ciphertext + id
    #declaramos la funcion hash y hasheamos el Ct con el ID
    hash = SHA256.new()
    hash.update(ct_hash_esperado)
    ct_hash_esperado = hash.digest()
    #Se valida si el hash recibido es igual al hash generado en estta funcion
    print('Validacion de Hctb =')
    print(compare_digest(ct_hash,ct_hash_esperado))
    #se desencapsula el Ct con la Sk y obtenemos el Pt
    plaintext_recovered = decrypt(secret_key, ciphertext)
    #connection.sendall(plaintext_recovered)
    #Se realiza la funcion KDF con el Pt y hash
    key = scrypt(plaintext_recovered, ct_hash, 16, N=2**14, r=8, p=1)
    return key, ct_hash[0:16]

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Inicializamos el socket y lo ponemos en Bind
HOST = sys.argv[1]
PORT = 5001
server_address = (HOST, PORT)
sock.bind(server_address)
sock.listen(1)
#Declaramos las rutas de los archivos
route_in='doc_enc2.enc'
route_out='doc_dec.txt'
#Estos valores son utlizados para recibir el documento
CHUNK_SIZE = 1024
len_chunk = CHUNK_SIZE
#Se declaran los ID
id_b = b'12.34.56.78'
id_d = b'87.65.43.21'
#Se declara el mensaje que es utilizado en la fase 2
mi = get_random_bytes(32)

while True:
    print('waiting for a connection')
    connection, client_address = sock.accept()
    amount_expected = 1088
    amount_received = 0

    try:

        #Imprimimos que se ha conectado el cliente
        print('client connected:', client_address)

        #FASE1
        key, iv= desencapsulado(id_b)

        #FASE2
        #Generamos la Pk para la firma con Dilithium
        public_key_sign, secret_key_sign = generate_keypair()
        #Enviamos al Cliente la llave publica
        connection.sendall(public_key_sign)

        #Recibimos el documento enmcriptado enviado por el cliente
        CHUNK_SIZE = 1024
        len_chunk = CHUNK_SIZE

        with open(route_in, "wb") as f:
            chunk = connection.recv(CHUNK_SIZE)
            while chunk:
                print("recibiendo...")
                f.write(chunk)
                if len_chunk < CHUNK_SIZE:
                    break
                else:
                    chunk = connection.recv(CHUNK_SIZE)
                    len_chunk = len(chunk)
        f.close()

        #Desencriptamos el documento recibido
        desencriptar(route_in, key, iv, route_out)

        #Tomamos el mensaje recibido
        f = open(route_in, 'rb')
        mensaje = f.read()
        f.close()

        #Creamos el bloque de firma
        signature = sign(secret_key_sign,mi)
        #Concatenamos el ID_C, el bloque de firma, el mensaje delcarado anteriormente y el mensaje
        msg_hash = id_d + signature + mi + mensaje

        #Hasheamos el mensaje anteriormente concatenado
        hash = SHA256.new()
        hash.update(msg_hash)
        msg_hash = hash.digest()

        t=1
        time.sleep(.5)
        #enviamos el mensaje
        #print(mi)
        connection.send(mi)
        #Enviamos el hasheo
        #print(msg_hash)
        connection.send(msg_hash)
        #Enviamos el bloque de firma
        #print(signature)
        connection.send(signature[0:1024])
        #print(".")
        time.sleep(.5)
        #print(".")
        connection.send(signature[1024:2044])

        #FINFASE2
        #time.sleep(t)

    finally:
        connection.close()
