from numpy import number
from pandas.core.dtypes import dtypes
import pandas as pd

ret_structure=pd.read_csv("D:/Temp/retail_structure.csv")

nwk_structure=pd.read_csv("D:/Temp/network_structure.csv")

elec_registers=pd.read_csv("D:/Temp/elec_registers.csv") # delete this line in prod as this table already there

ret_structure1 = pd.merge(ret_structure,elec_registers.drop(columns=['LogicalRegisterNumber','RateType','State','RetailTariffType','NetworkTariff','NetworkTariffType']),
                            how='inner',left_on='RetailTariff',right_on='RetailTariff')