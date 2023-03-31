import sys, getopt
sys.path.append('.')
import FaBo9Axis_MPU9250
import os.path
import time
import datetime
import math
import operator
import socket
from numpy import *
import os
#import paho.mqtt.client as mqttClient
import json
import random

sensor_id = b'127.125.178'
magnitud=0.0
magnitudG = 0.0
media=0.0
d_e=0.0
suma=0.0
magnitud_t = 0.0
magnitudG_t = 0.0
j = 0

mpu9250 = FaBo9Axis_MPU9250.MPU9250()

sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST_SOCK = sys.argv[1]
PORT_SOCK = 5005
server_sock_address = (HOST_SOCK, PORT_SOCK)
print('connecting to {} port {}'.format(*server_sock_address))
sock1.connect(server_sock_address)

while True:

    accel = mpu9250.readAccel()
    magnitud = math.sqrt(((accel['x'])**2)+((accel['y'])**2)+((accel['z'])**2))
    gyro = mpu9250.readGyro()
    magnitudg = math.sqrt(((gyro['x'])**2)+((gyro['y'])**2)+((gyro['z'])**2))


    if j==0:
            f = open('magnitudes.txt','w')
            f.write(str(magnitudg) + '\n' + str(magnitud))
            f.close
            j = j + 1
    else:
            f = open('magnitudes.txt','a')
            f.write('\n'+str(magnitudg) + '\n' + str(magnitud))
            f.close
            j = j + 1


    time.sleep(0.01)
    if j == 150: break

f = open('magnitudes.txt','r')
read_file = f.readlines()
f.close

with open('magnitudes.txt', 'rb') as f:
    sock1.sendfile(f)
    #print('documento enviado')
f.close()

pos = 0
pos1 = 1
aux = 0
n = 0
m = 90
apuntador = 0
apuntado = 1
magnitud_t = 0.0
magnitudg_t = 0.0

while True:
        for i in range (1,90):
                magnitud_t = magnitud_t + float(read_file[pos1])
                magnitudg_t = magnitudg_t + float(read_file[n])
                n = n + 2
                pos1 = pos1 + 2
                #print n
        if m == 140:
                break
        if apuntador == 0:
                f=open('giroscopio.txt','w')
                f.write(str(magnitudg_t) + '\n')
                f.close
                f=open('acelerometro.txt','w')
                f.write(str(magnitud_t) + '\n')
                f.close
                magnitudG_t = 0.0
                magnitud_t = 0.0
                apuntador = apuntador + 2
                apuntado = apuntado + 2
                n = apuntador
                pos1 = apuntado
        else:
                f=open('giroscopio.txt','a')
                f.write(str(magnitudg_t) + '\n')
                f.close
                f=open('acelerometro.txt','a')
                f.write(str(magnitud_t) + '\n')
                f.close
                magnitudG_t = 0.0
                magnitud_t = 0.0
                apuntador = apuntador + 2
                apuntado = apuntado + 2
                n = apuntador
                pos1 = apuntado
        m = m + 1

pos=0
pos1=1

for i in range(0, 50):
    #sock1.send(read_file[pos])
    #time.sleep(0.01)
    #sock1.send(read_file[pos1])
    suma=suma + float(read_file[pos1])
    pos=pos+1
    pos1=pos1+2

media=suma/j
ayuda=0.0
pos1=1
for i in range(0,j):
    ayuda= (float(read_file[pos1])-media)**2 + ayuda
    pos1=pos1+2
d_e=math.sqrt(ayuda/j)
print('media ', media)
print(d_e)
data = sock1.recv(1)
print(data)
if data==b'1':
        #os.system("python senseUbi.py")
#        print ('data es 1')
        sock1.send(sensor_id)
else:
        sock1.close()
#        print (data)
