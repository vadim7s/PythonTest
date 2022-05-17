'''
Found on stackoverflow - example how to chunk a big merge
'''

import pandas as pd

df1 = pd.read_csv("D:/Temp/file1.csv")
df2 = pd.read_csv("D:/Temp/file2.csv")
#df2_key = df2.pod

# creating a empty bucket to save result
df_result = pd.DataFrame(columns=(df1.columns.append(df2.columns)).unique())
df_result.to_csv("D:/Temp/df3.csv",index_label=False)


# deleting df2 to save memory
del(df2)

def preprocess(x):
    df2=pd.merge(df1,x, how="inner",left_on = "Key_Col", right_on = "Key_Col")
    df2.to_csv("D:/Temp/df3.csv",mode="a",header=False,index=False)
    print('length of joined df in the chunk: ',len(df2),' columns: ',df2.columns)

reader = pd.read_csv("D:/Temp/file2.csv", chunksize=2) # chunksize depends with you colsize
[preprocess(r) for r in reader]