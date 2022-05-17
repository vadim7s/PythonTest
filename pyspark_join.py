from numpy import number
from pandas.core.dtypes import dtypes
import pandas as pd

from pyspark.sql import SparkSession
from pyspark import SparkContext, SparkConf

# context config/setup 
sc = SparkContext(conf=SparkConf().setMaster('local[8]'))
spark = SparkSession.builder.getOrCreate()
spark.conf.set("spark.sql.execution.arrow.enabled", "true")

t1=spark.createDataFrame(pd.read_csv("D:/Temp/retail_structure.csv"))
t2=spark.createDataFrame(pd.read_csv("D:/Temp/elec_registers.csv").drop(columns=['LogicalRegisterNumber','RateType','State','RetailTariffType','NetworkTariff','NetworkTariffType'])) # delete this line in prod as this table already there


#nwk_structure=pd.read_csv("D:/Temp/network_structure.csv")


ret_structure1 = t1.join(t2,t1['RetailTariff']==t2['RetailTariff']) 

ret_structure1.toPandas().to_csv("D:/Temp/join.csv")