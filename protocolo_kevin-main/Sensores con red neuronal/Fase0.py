import random
import time
import numpy as np
import keras.models
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Flatten
from keras.layers import Dropout
from keras.layers import LSTM
from keras.layers import ConvLSTM2D
from keras.utils import to_categorical
from matplotlib import pyplot
import FaBo9Axis_MPU9250


def obtener_datos():
    dato = [[], [], [], [], [], []]
    mpu9250 = FaBo9Axis_MPU9250.MPU9250()
    for j in range(150):
        accel = mpu9250.readAccel()
        gyro = mpu9250.readGyro()
        datos = [accel['x'], accel['y'], accel['y'], gyro['x'], gyro['y'], gyro['z']]
        for a, d in enumerate(datos):
            dato[a].append(d)
        time.sleep(0.01)
    return dato


def obtener_datos_externos():
    dato = [[], [], [], [], [], []]
    mpu9250 = FaBo9Axis_MPU9250.MPU9250()
    for j in range(150):
        accel = mpu9250.readAccel()
        gyro = mpu9250.readGyro()
        datos = [accel['x'], accel['y'], accel['y'], gyro['x'], gyro['y'], gyro['z']]
        for a, d in enumerate(datos):
            dato[a].append(d)
        time.sleep(0.01)
    return dato


def comparacion_nn():
    B = obtener_datos()
    C = obtener_datos_externos()
    X = B + C
    X_t = np.array([np.array(X).T])
    X = X_t.reshape((X_t.shape[0], 10, 1, 15, X_t.shape[2]))
    pred = model.predict_classes(X)
    if pred == 0:
        resultado = 'Aceptado'
    else:
        resultado = 'Rechazado'
    return resultado


model = keras.models.load_model('convlstm_sensors.h5')
comparacion_nn()
