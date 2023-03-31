from mpu6050 import mpu6050
import time
import datetime
from itertools import count
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


# En algunos casos es más fácil utilizar la librería mpu6050, pero se puede cambiar para utilizar la FaBo9Axis_MPU9250
# import FaBo9Axis_MPU9250
# mpu9250 = FaBo9Axis_MPU9250.MPU9250()


def save_data_1(reg=100):
    ''' Solamente guarda los datos en archivos .txt independientes. Toma como argumento el número de muestras que se desean tomar. No hay ningún tiempo de espera. '''
    sensor = mpu6050(0x68, bus=1)
    names = ['acc_x_1', 'acc_y_1', 'acc_z_1', 'gyro_x_1', 'gyro_y_1', 'gyro_z_1']
    for n in names:
        globals()[n] = open(n + '.txt', 'w')
    for i in range(reg):
        for j in range(150):
            # accel = mpu9250.readAccel()
            # gyro = mpu9250.readGyro()
            accel = sensor.get_accel_data()
            gyro = sensor.get_gyro_data()
            datos = [accel['x'], accel['y'], accel['y'], gyro['x'], gyro['y'], gyro['z']]
            for n, d in zip(names, datos):
                globals()[n].write(str(d) + '\t')
        for n in names:
            globals()[n].write('\n')
    for n in names:
        globals()[n].close
    print('Datos guardados')


def plot_graphs_1():
    ''' Grafica en tiempo real mediante una animación
    los datos obtenidos del eje x del acelerómetro.'''
    plt.style.use('fivethirtyeight')

    sensor = mpu6050(0x68, bus=1)
    X = list()
    Y = list()
    for j in range(150):
        accel = sensor.get_accel_data()
        X.append(j)
        Y.append(accel['x'])
        time.sleep(1)
        print(j)

    ani = FuncAnimation(plt.gcf(), animate, interval=1000)

    plt.tight_layout()
    plt.show()


def animate(i):
    plt.cla()
    plt.plot(X, Y, label='acc_x')
    plt.tight_layout()


def save_and_plot_1(reg=100):
    ''' Guarda los datos en archivos .txt independientes especificando que se trata del sensor 1. Toma como argumento el número de muestras que se desean tomar. Entre cada toma de muestra se espera 10 milisegundos. Al final gráfica cada eje del acelerómetro y del giroscopio como series de tiempo para comprender mejor los movimientos realizados durante la toma de muestras. '''
    from datetime import datetime
    now = datetime.now()
    sensor = mpu6050(0x68, bus=1)
    num = list(range(150 * reg))
    dato = [[], [], [], [], [], []]
    names = ['acc_x_1', 'acc_y_1', 'acc_z_1', 'gyro_x_1', 'gyro_y_1', 'gyro_z_1']
    # name = [ac_x_1, ac_y_1, ac_z_1, gyr_x_1, gyr_y_1, gyr_z_1]
    for n in names:
        globals()[n] = open(n + now.strftime(" %d-%m-%Y %H-%M") + '.txt', 'w')
    for i in range(reg):
        for j in range(150):
            # accel = mpu9250.readAccel()
            # gyro = mpu9250.readGyro()
            accel = sensor.get_accel_data()
            gyro = sensor.get_gyro_data()
            datos = [accel['x'], accel['y'], accel['y'], gyro['x'], gyro['y'], gyro['z']]
            for a, d in enumerate(zip(names, datos)):
                globals()[d[0]].write(str(d[1]) + '\t')
                dato[a].append(d[1])
            time.sleep(0.01)
        for n in names:
            globals()[n].write('\n')
    for n in names:
        globals()[n].close
    print('Datos guardados')

    fig, axs = plt.subplots(3, 2, sharex=True)
    fig.suptitle('Sensor 1')
    axs[0, 0].plot(num, dato[0], 'mediumblue')
    axs[0, 0].set_title('Acelerómetro')
    axs[1, 0].plot(num, dato[1], 'darkviolet')
    axs[2, 0].plot(num, dato[2], 'forestgreen')
    axs[0, 1].plot(num, dato[3], 'deepskyblue')
    axs[0, 1].set_title('Giroscopio')
    axs[1, 1].plot(num, dato[4], 'gold')
    axs[2, 1].plot(num, dato[5], 'red')
    fig.savefig(now.strftime(" %d-%m-%Y %H-%M") + '.png')

    # fig.show()


def save_and_plot_2(reg=100):
    """ Guarda los datos en archivos .txt independientes especificando que se trata del **sensor 2**. Toma como
    argumento el número de muestras que se desean tomar. Entre cada toma de muestra se espera 10 milisegundos. Al
    final gráfica cada eje del acelerómetro y del giroscopio como series de tiempo para comprender mejor los
    movimientos realizados durante la toma de muestras. """
    from datetime import datetime
    now = datetime.now()
    names = ['acc_x_2', 'acc_y_2', 'acc_z_2', 'gyro_x_2', 'gyro_y_2', 'gyro_z_2']
    sensor = mpu6050(0x68, bus=1)
    num = list(range(150 * reg))
    dato = [[], [], [], [], [], []]
    for n in names:
        globals()[n] = open(n + now.strftime(" %d-%m-%Y %H-%M") + '.txt', 'w')
    for i in range(reg):
        for j in range(150):
            # accel = mpu9250.readAccel()
            # gyro = mpu9250.readGyro()
            accel = sensor.get_accel_data()
            gyro = sensor.get_gyro_data()
            datos = [accel['x'], accel['y'], accel['y'], gyro['x'], gyro['y'], gyro['z']]
            for a, d in enumerate(zip(names, datos)):
                globals()[d[0]].write(str(d[1]) + '\t')
                dato[a].append(d[1])
            time.sleep(0.01)
        for n in names:
            globals()[n].write('\n')
    for n in names:
        globals()[n].close
    print('Datos guardados')

    fig, axs = plt.subplots(3, 2, sharex=True)
    fig.suptitle('Sensor 2')
    axs[0, 0].plot(num, dato[0], 'mediumblue')
    axs[0, 0].set_title('Acelerómetro')
    axs[1, 0].plot(num, dato[1], 'darkviolet')
    axs[2, 0].plot(num, dato[2], 'forestgreen')
    axs[0, 1].plot(num, dato[3], 'deepskyblue')
    axs[0, 1].set_title('Giroscopio')
    axs[1, 1].plot(num, dato[4], 'gold')
    axs[2, 1].plot(num, dato[5], 'red')
    fig.savefig(now.strftime(" %d-%m-%Y %H-%M") + '.png')


# Se corre la función para guardar los datos del sensor 1.   
save_and_plot_1(100)
