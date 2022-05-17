'''
very simple example of using database package to extract data from Hana and/or MDS
'''

import pandas as pd
import database
#my_table = database.df_from_sql('HANA',"select top 10 * from A30001596.GEEKII_AGL_ALL_CONTRACT_DETAILS")
my_table = database.df_from_sql('MDS','select * from pricing.pricing_clv_fee_offset')
print(my_table)

