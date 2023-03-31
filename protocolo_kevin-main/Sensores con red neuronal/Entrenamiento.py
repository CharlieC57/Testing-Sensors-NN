# convlstm model
from numpy import mean
from numpy import std
from numpy import dstack
from pandas import read_csv
import keras.models
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Flatten
from keras.layers import Dropout
from keras.layers import LSTM
from keras.layers import TimeDistributed
from keras.layers import ConvLSTM2D
from keras.utils import to_categorical
from matplotlib import pyplot
from datetime import datetime

# Carga un solo archivo como una matriz numpy
def load_file(filepath):
    dataframe = read_csv(filepath, header=None, delim_whitespace=True)
    return dataframe.values

# carga una lista de archivos y regresa como una matriz numérica 3d
def load_group(filenames, prefix=''):
    loaded = list()
    for name in filenames:
        data = load_file(prefix + name)
        loaded.append(data)
    # apila un grupo para que las características sean de 3 dimensiones
    loaded = dstack(loaded)
    return loaded

# carga el dataset de un grupo, entrenamiento o prueba
def load_dataset_group(group, prefix=''):
    filepath = prefix + group + '/Inertial Signals/'
    # carga todos los archivos como un arreglo
    filenames = list()
    # aceleración sensor 1
    filenames += ['acc_x_1_'+group+'.txt', 'acc_y_1_'+group+'.txt', 'acc_z_1_'+group+'.txt']
    # giroscopio sensor 1
    filenames += ['gyro_x_1_'+group+'.txt', 'gyro_y_1_'+group+'.txt', 'gyro_z_1_'+group+'.txt']
    # aceleración sensor 2
    filenames += ['acc_x_2_'+group+'.txt', 'acc_y_2_'+group+'.txt', 'acc_z_2_'+group+'.txt']
    # giroscopio sensor 2
    filenames += ['gyro_x_2_'+group+'.txt', 'gyro_y_2_'+group+'.txt', 'gyro_z_2_'+group+'.txt']
    # carga los datos de entrada
    X = load_group(filenames, filepath)
    # carga las clases de salida
    y = load_file(prefix + group + '/y_'+group+'.txt')
    return X, y

# carga los datasets, devuelve datos y etiquetas de entrenamiento y prueba
def load_dataset(prefix=''):
    # carga todo el entrenamiento
    trainX, trainy = load_dataset_group('train', prefix + 'SensorDataset/')
    print(trainX.shape, trainy.shape)
    # carga todo el test
    testX, testy = load_dataset_group('test', prefix + 'SensorDataset/')
    print(testX.shape, testy.shape)
    # valores de clase de compensación cero
    trainy = trainy - 1
    testy = testy - 1
    # codificación one hot en y
    trainy = to_categorical(trainy)
    testy = to_categorical(testy)
    print(trainX.shape, trainy.shape, testX.shape, testy.shape)
    return trainX, trainy, testX, testy

# entrena y evalua el modelo
def evaluate_model(trainX, trainy, testX, testy):
    verbose, epochs, batch_size = 0, 25, 64
    n_timesteps, n_features, n_outputs = trainX.shape[1], trainX.shape[2], trainy.shape[1]
    # reshape en subsecuencias (muestras, pasos de tiempo, filas, columnas, canales)
    n_steps, n_length = 10, 15
    trainX = trainX.reshape((trainX.shape[0], n_steps, 1, n_length, n_features))
    testX = testX.reshape((testX.shape[0], n_steps, 1, n_length, n_features))
    # define modelo
    model = Sequential()
    model.add(ConvLSTM2D(filters=64, kernel_size=(1,3), activation='relu', input_shape=(n_steps, 1, n_length, n_features)))
    model.add(Dropout(0.5))
    model.add(Flatten())
    model.add(Dense(100, activation='relu'))
    model.add(Dense(n_outputs, activation='softmax'))
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    # entrena la red
    model.fit(trainX, trainy, epochs=epochs, batch_size=batch_size, verbose=verbose)
    now = datetime.now()
    model.save('convlstm_sensors'+now.strftime(" %d-%m-%Y %H-%M-%S")+'.h5')
    # evalua modelo
    _, accuracy = model.evaluate(testX, testy, batch_size=batch_size, verbose=0)
    return accuracy

# resumir puntuaciones
def summarize_results(scores):
    print(scores)
    m, s = mean(scores), std(scores)
    print('Precisión: %.3f%% (+/-%.3f)' % (m, s))

# correr un experimento (10 veces)
def run_experiment(repeats=10):
    # cargar los datos
    trainX, trainy, testX, testy = load_dataset()
    # repetir experimento
    scores = list()
    for r in range(repeats):
        score = evaluate_model(trainX, trainy, testX, testy)
        score = score * 100.0
        print('Exp-#%d: %.3f' % (r+1, score))
        scores.append(score)
    # resumen de resultados
    summarize_results(scores)

# correr un experimento
run_experiment()
