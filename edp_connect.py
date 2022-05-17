'''
This is an example on how to connect to EDP and run a simple query 
with Python

'''


import database
qry='SELECT TOP (10)* FROM [commercial].[dim_SalesMart_cr]'
sample_table = database.df_from_sql('EDP',qry)
print(sample_table.head(3))