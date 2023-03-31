'''
El siguiente programa sera corrido en el Nodo Coordinador B
Se deben descargar las bibliotecas pycryptodome y pqcrypto
'''
import socket
import sys
import os
import pqcrypto
import time
import requests

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from secrets import compare_digest
#from pqcrypto.kem.kyber768 import generate_keypair, encrypt, decrypt
from pqcrypto.sign.dilithium2 import generate_keypair, sign, verify
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes


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
server_address = ('127.0.0.1', 5001)
print('connecting to {} port {}'.format(*server_address))
sock.connect(server_address)
#declaramos rutas a utilizar
route_in = 'example.txt'
route_out = 'doc_enc.enc'
route_out2 = 'doc_dec_2.txt'
CHUNK_SIZE = 1024
#declaramos IDs
id_b =b'12.34.56.78'
id_d = b'87.65.43.21'
ip_c = '192.168.100.59'

try:
    #FASE1
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
    with open(route_out, 'rb') as f:
        sock.sendfile(f)
        #print('documento enviado')
    f.close()

    #Leemos el mensaje del archivo 
    f = open(route_out, 'rb')
    mensaje = f.read()
    f.close()

    #recibimos el mensaje unico
    mi = sock.recv(32)
    #recibimos el bloque de firma
    signature = sock.recv(2044)
    #recibimos el mensaje hasheado
    msg_hash = sock.recv(256)
    msg_hash_esperado = id_d + signature + mi + mensaje

    #print(msg_hash_esperado)
    hash = SHA256.new()
    hash.update(msg_hash_esperado)
    msg_hash_esperado = hash.digest()
    
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
    #requests.post(direccion,data)
    #FINFASE3

finally:
    sock.close()
