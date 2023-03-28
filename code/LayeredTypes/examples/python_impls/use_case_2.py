from random import randrange
from builtins import len, print

def create_dataset(num_cols, num_rows):
    dataset = []
    for i in range(num_rows):
        row = []
        for j in range(num_cols):
            row.append(randrange(100))
        dataset.append(row)
    return dataset

def add_rows(dataset, num_rows):
    for i in range(num_rows):
        row = []
        for j in range(len(dataset[0])):
            row.append(randrange(100))
        dataset.append(row)
    return dataset

def add_cols(dataset, num_cols):
    for i in range(len(dataset)):
        for j in range(num_cols):
            dataset[i].append(randrange(100))
    return dataset

# Reduce the number of cols in the dataset to num_cols
def reduce_cols(dataset, num_cols):
    for i in range(len(dataset)):
        dataset[i] = dataset[i][:num_cols]
    return dataset

def sample(dataset, num_rows):
    return dataset[:num_rows]

def train(dataset):
    print("Training on dataset of size: ", len(dataset), "x", len(dataset[0]))