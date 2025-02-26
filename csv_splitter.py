import os
import csv
import pandas as pd

chunk_no = 0


for chunk in pd.read_csv('C:\\Users\\isaac\\Desktop\\GenAI\\Assignment_1\\ngram-recommender\\output.csv', chunksize= 150000):
    chunk_no += 1
    #if chunk_no == 1:
    #    chunk.to_csv('C:\\Users\\isaac\\Desktop\\GenAI\\Assignment_1\\ngram-recommender\\output1.csv')
    if chunk_no == 2:
        chunk.to_csv('C:\\Users\\isaac\\Desktop\\GenAI\\Assignment_1\\ngram-recommender\\output2.csv')
    