import pickle
import numpy
import matplotlib.pyplot


FILE_NAME = 'data.pickle'

with open(FILE_NAME, 'rb') as file:
    data = pickle.load(file)

data_array = numpy.array(data)

num_bins = data_array.max()

matplotlib.pyplot.hist(data_array, bins=num_bins, density=True, histtype='step')
matplotlib.pyplot.show()


def printArrayData():
    #todo
    pass