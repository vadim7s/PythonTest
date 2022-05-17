'''
This module is to create
1. Retail tariff structure at the hourly level
2. Network structure at the hourly level
applcation of these is only possible to a small-ish set of 
conracts/NMIs at a time (or resulting tables become too large)

tqdm library allows to add progress bars. Pandas version must be 1.2.5 not later
'''

from numpy import number
from pandas.core.dtypes import dtypes
import database
import pandas as pd
import holidays
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tqdm import tqdm  #trick to get progress bar: normal apply() is replaced wit progress_apply() or progress_apply(lambda x: x) is added to other df ops like merge
tqdm.pandas()


retail_tariff_set = "select distinct BaselineRetailTariff as RetailTariff from AGL_PRICING.dbo.CONTRACT_ATTRIBUTE" #where patch='UNITED'"
network_tariff_set = "select distinct BaselineNetworkTariffCode as NetworkTariff from AGL_PRICING.dbo.CONTRACT_ATTRIBUTE" # where patch='UNITED'"
    

# these queries below create very crude structures with all possible timeband periods
# then you would beed to explode them by 365d x 24h
# it is important to apply timeband and weekend/PH rules to only leave 
# certain subset of records from what is originally extracted by the queries.

ret_str_query = "select tbc.retail_tariff as RetailTariff" \
                ",tbc.retail_component,t.code as timeband" \
                ",t.date_from,t.date_to,t.time_from,t.time_to,t.weekday," \
                "s.class, s.DefaultNetworkTariff,s.Patch,s.KVA,s.ret_tariff_comp_description,s.RetailTariffType," \
                "s.retail_component_l1,s.retail_component_l2,s.retail_component_l3 " \
                "from pricing.pricing_timebands t " \
                "inner join " \
                "(SELECT retail_tariff_class_patch_id_Code as retail_tariff" \
                ",tariff_component_Code as retail_component,u.tbs as timeband " \
                "FROM AGL_MDS.pricing.pricing_retail_tariff_component_timeband " \
                "unpivot  (tbs for tb in (tb1_Code,tb2_Code,tb3_Code,tb4_Code,tb5_Code,tb6_Code,tb7_Code,tb8_Code,tb9_Code,tb10_Code)) u " \
                "where state='Active' and VersionFlag='Active') tbc " \
                "on tbc.timeband=t.code and t.VersionFlag = 'Active' and t.State = 'Active'" \
                "inner join (" \
                "select c.Name as ret_tariff_comp_description, c.code as ret_tariff_component," \
                "c.retail_component_l1,c.retail_component_l2,c.retail_component_l3,cm.class," \
                "cm.Retail_Tariff_Code,cm.Patch,cm.KVA,cm.RetailTariffStructure,cm.DefaultNetworkTariff,cm.RetailTariffType " \
                "from pricing.pricing_retail_tariff_components c " \
                "inner join (" \
                "select Code as Retail_Tariff_Code," \
                "patch_id_Code as Patch," \
                "retail_tariff_id as RetailTariffStructure," \
                "Class_code as class," \
                "retail_tariff_type_Code as RetailTariffType," \
                "default_network_tariff_Code as DefaultNetworkTariff," \
                "[KVA demand_Code] as KVA," \
                "u.comps as retail_component " \
                "from AGL_MDS.pricing.pricing_retail_tariff " \
                "unpivot(comps for comp in (c1_Code,c2_Code,c3_Code,c4_Code,c5_Code,c6_Code,c7_Code,c8_Code,c9_Code,c10_Code)) u " \
                "where State = 'Active' and VersionFlag = 'Active') cm " \
                "on cm.retail_component=c.Code) s " \
                "on s.Retail_Tariff_Code=tbc.retail_tariff and s.ret_tariff_component=tbc.retail_component " 
                

nwk_str_query = "select tbc.network_tariff as NetworkTariff,tbc.network_component," \
                "t.code as timeband,t.date_from,t.date_to,t.time_from ,t.time_to,t.weekday" \
                ",s.class, s.Patch,s.KVA,s.HolidayAsWeekend as holiday_as_weekend,s.NetworkType," \
                "s.network_component_l1,s.network_component_l2,s.network_component_l3 " \
                "from pricing.pricing_timebands t " \
                "inner join " \
                "(SELECT " \
                "network_tariff_patch_id_Code as network_tariff" \
                ",tariff_component_Code as network_component" \
                ",u.tbs as timeband " \
                "FROM AGL_MDS.pricing.pricing_network_tariff_component_timeband " \
                "unpivot  (tbs for tb in (tb1_Code,tb2_Code,tb3_Code,tb4_Code,tb5_Code,tb6_Code,tb7_Code,tb8_Code,tb9_Code,tb10_Code)) u " \
                "where state='Active' and VersionFlag='Active') tbc " \
                "on tbc.timeband=t.code and t.VersionFlag = 'Active' and t.State = 'Active' " \
                "inner join " \
                "(select c.code as nwk_tariff_component," \
                "c.network_component_l1,c.network_component_l2,c.network_component_l3,cm.class," \
                "cm.NetworkTariff,cm.Patch,cm.NetworkTariffStructure,cm.KVA,cm.HolidayAsWeekend,cm.NetworkType " \
                "from pricing.pricing_network_tariff_components c " \
                "inner join ( " \
                "select Code as NetworkTariff," \
                "netw_tariff_structure_Code as NetworkType," \
                "patch_id_Code as Patch," \
                "network_tariff_id as NetworkTariffStructure," \
                "netw_class_code as class," \
                "netw_holiday_as_weekend as HolidayAsWeekend," \
                "[KVA demand_Code] as KVA," \
                "u.comps as network_component " \
                "from AGL_MDS.pricing.pricing_network_tariff " \
                "unpivot(comps for comp in (c1_Code,c2_Code,c3_Code,c4_Code,c5_Code,c6_Code,c7_Code,c8_Code,c9_Code,c10_Code)) u " \
                "where State = 'Active' and VersionFlag = 'Active') cm " \
                "on cm.network_component=c.Code " \
                ") s on s.NetworkTariff=tbc.Network_tariff and s.nwk_tariff_component=tbc.network_component"
                
hana_dst_qry ="Select STARTDATE as DST_STARTDATE,ENDDATE as DST_ENDDATE," \
                "'OFF' as DST, year(STARTDATE) as Year " \
                "From DATAINT.TBL_CALENDARTIMEOFFSET " \
                "WHERE CALENDARCODE='VIC' AND MONTH(STARTDATE)=4"

patch_qry = "select Code as patch,state_code as state," \
            "case when fuel_Code='01' then 'Electricity' else 'Gas' end as fuel " \
            "from AGL_MDS.pricing.pricing_patch where State = 'Active' and VersionFlag = 'Active'"

#########################################################
#
#         Functions defining if timebands apply
#
#########################################################

def flag_DST(df):

    if df['date'] >= df['DST_STARTDATE'] and df['date'] <= df['DST_ENDDATE']:
        return df['DST']
    else: return 'ON'

def date_applies(df):
#this function adds a column which flags if this timeband applies to this date
    if df['date_from'] in ("AEST-DST ON","AEST-DST OFF"):
        if (df['AEDT_Flag'] == "ON" and df['date_from'] == "AEST-DST ON") or (df['AEDT_Flag']=="OFF" and df['date_from'] =="AEST-DST OFF"):
            return True
        else:
            return False
    else:
        if df['date_from'] =="Any":
            return True
        else:
            if df['date_from']<df['date_to']:
                if df['date'].strftime('%m-%d') >=df['date_from'] and df['date'].strftime('%m-%d') <=df['date_to']:
                    return True
                else:
                    return False
            else:
                if df['date'].strftime('%m-%d')<=df['date_to'] and df['date'].strftime('%m-%d')>=df['date_from']:
                    return True
                else:
                    return False

def weekday_applies(df):
# this logic decides whether this row of tariff structure applies to this record using weekday column of tariff structure 
    if df['weekday'] == "Anyday":
        return True
    else:
        if df['weekday'] == "Weekday":
            if df['weekend'] == False:
                if df['PH_Flag']==False:
                    return True
                else:
                    if df['holiday_as_weekend']==False:
                        return True
                    else:
                        return False
            else:
                return False
        else:
            if df['weekend']:
                return True
            else:
                if df['holiday_as_weekend'] and df['PH_Flag']:
                    return True
                else:
                    return False

def time_applies(df):
    # This function flags applicable timband combinations using time from and to
    if df['time_from']=="Any" or df['time_to']=="Any":
        return True
    else:
        #pre-calc variables for multiple use
        time_from = pd.to_numeric(df['time_from'])
        time_to = pd.to_numeric(df['time_to'])
        this_hour = pd.to_numeric(df['hour'])
        if time_from <= time_to:
            if this_hour >= time_from and this_hour <= time_to:
                return True
            else:
                return False
        else:
            if this_hour <= time_to or this_hour >= time_from:
                return True
            else:
                return False

def retail_component_group(df):
# this function is to create a column in retail tariff
# structure to indicate what component group this is
# which is used in component mapping with network structure 
    if df['retail_component_l1']=="Fixed":
        return "Fixed"
    elif df['retail_component_l3']=="Solar":
        return "Solar"
    elif df['retail_component_l3']=="Controlled Load" or df['RetailTariffType']=="Controlled Load":
        return "CL"
    elif df['retail_component_l3']=="Demand":
        return "Demand"
    else:
        return "Usage"

def network_component_group(df):
# this function is to create a column in network tariff
# structure to indicate what component group this is
# which is used in component mapping with retail structure 
    if df['network_component_l1']=="Fixed":
        return "Fixed"
    elif df['network_component_l3']=="Solar":
        return "Solar"
    elif df['network_component_l3']=="Controlled Load" or df['NetworkType']=="Controlled Load":
        return "CL"
    elif df['network_component_l3']=="Demand":
        return "Demand"
    else:
        return "Usage"

###############################################################
#
#     create retail structure by running source queries
#     to MDS and hana
#
###############################################################

print("Began pulling tariff structure data...")

#create a dataframe for past year (excl feb29) for a row for each 24 hrs (0..23)
today = datetime.now().date()
start_date = today + relativedelta(years=-1)
current_date = start_date

d = []
while current_date < today:
    for i in range(24):
        if current_date.month != 2 or current_date.day != 29: 
            d.append({'date': pd.to_datetime(current_date),'hour': i})
    current_date = current_date + relativedelta(days=1)
dates_hours = pd.DataFrame(d)

del d

dates_hours['tmp'] = 1

dst = database.df_from_sql('HANA',hana_dst_qry)
patches = database.df_from_sql('MDS',patch_qry)

# extract structure
ret_structure = database.df_from_sql('MDS',ret_str_query)
retail_tariff_set = database.df_from_sql('AGL_PRICING',retail_tariff_set)

# wash structure against relevant tariffs, i.e limit to tariffs applicable to what you do
ret_structure = pd.merge(ret_structure,retail_tariff_set,how='inner',left_on=['RetailTariff'],right_on=['RetailTariff'])
#print(ret_structure.dtypes)
#print('Length of retail structure after limiting to relevant tariffs: ',len(ret_structure))
ret_structure['tmp'] = 1
ret_structure = pd.merge(ret_structure, dates_hours, on=['tmp']).drop(columns= ['tmp'])

#print(ret_structure.dtypes)

#join with DST dataset to get AEDT
ret_structure['Year']=pd.DatetimeIndex(ret_structure['date']).year
#print('Length of retail structure before join with DST: ',len(ret_structure))
ret_structure = pd.merge(ret_structure,dst,how='inner',left_on=['Year'],right_on=['YEAR']).drop(columns= ['Year','YEAR'])

#apply Daylight Saving time logic
print('Flagging daylight saving...')
ret_structure['AEDT_Flag'] = ret_structure.progress_apply(flag_DST, axis = 1)
ret_structure.drop(columns = ['DST','DST_STARTDATE','DST_ENDDATE'],inplace=True)

# get state
ret_structure = pd.merge(ret_structure,patches,how='inner',left_on=['Patch'],right_on=['patch']).drop(columns=['patch','fuel'])
#print('Length of retail structure after join with Patches: ',len(ret_structure))

# get public holidays

# years from and to can only be one year apart as we deal with 365d period
# accordingly we only need 2 year variables - year_from and year_to
# if this chanages to a longer period, you may need to add year_3 
# to have full list of years to use with years = [...] below
year_from = ret_structure['date'].min().year 
year_to = ret_structure['date'].max().year 

aus_holiday_table=pd.DataFrame()
for state in ['ACT','VIC','NSW','QLD','WA']:
    holidays_list = [x[0] for x in holidays.Australia(years=[year_from,year_to],prov=state).items()]
    holidays_list = pd.DataFrame(holidays_list)
    holidays_list['state']=state
    aus_holiday_table = pd.concat([aus_holiday_table,holidays_list],0)
aus_holiday_table.rename(columns={aus_holiday_table.columns[0]: 'date'},inplace=True)
aus_holiday_table['date'] = pd.to_datetime(aus_holiday_table['date'], format= '%Y/%m/%d')
aus_holiday_table['PH_Flag']=True

ret_structure = pd.merge(ret_structure,aus_holiday_table,how='left',left_on=['date','state'],right_on=['date','state'])
ret_structure['PH_Flag'].fillna(False,inplace=True)

# define a flag for date being weekend
ret_structure['weekend'] = ret_structure['date'].dt.day_name().isin(['Saturday', 'Sunday'])

#print('Length of retail structure after join with Public Holidays: ',len(ret_structure))
print("Completed column preparation for retail timeband application...")

################################################################################
#
#  determine if timebands apply as we have public holidays and daylight saving
#  that logic is defined by functions above
#
################################################################################
ret_structure['holiday_as_weekend']=True  #retail tariff has this regardless of tariff
print('Applying date...')
ret_structure['date_applies'] = ret_structure.progress_apply(date_applies, axis = 1)
ret_structure = ret_structure[(ret_structure['date_applies'])]
print('Applying weekday...')
ret_structure['weekday_applies'] = ret_structure.progress_apply(weekday_applies, axis = 1)			  
ret_structure = ret_structure[(ret_structure['weekday_applies'])]
print('Applying time/hour...')
ret_structure['time_applies'] = ret_structure.progress_apply(time_applies, axis = 1)			  
#  filter only applicable timband applications/rows based on columns created above
ret_structure = ret_structure[(ret_structure['time_applies'])]
#print('Length of retail structure after taking only applicable timebands: ',len(ret_structure))
# add component group column for mapping to network
print('Applying component group...')
ret_structure['component_group'] = ret_structure.progress_apply(retail_component_group,axis =1)
ret_structure.drop(columns = ['Patch','class','timeband','date_from','date_to','time_from','time_to',
                                'weekday','AEDT_Flag','PH_Flag','weekend','holiday_as_weekend',
                                'date_applies','weekday_applies','time_applies'],inplace=True)

print("Completed retail structure... ", len(ret_structure)," rows")

##############################################################################
#
#     create network structure by running source queries
#     to MDS and hana
#
##############################################################################

nwk_structure = database.df_from_sql('MDS',nwk_str_query)
network_tariff_set = database.df_from_sql('AGL_PRICING',network_tariff_set)
# limit to tariffs in tariff set, i.e. contracts you process at a time to make it more efficient
nwk_structure = pd.merge(nwk_structure,network_tariff_set,how='inner',on=['NetworkTariff'])

#explode into 365 x 24
nwk_structure['tmp'] = 1
nwk_structure = pd.merge(nwk_structure, dates_hours, on=['tmp']).drop(columns= ['tmp'])

#print('Length of network structure before any joins: ',len(nwk_structure))
nwk_structure = pd.merge(nwk_structure,patches,how='inner',left_on=['Patch'],right_on=['patch']).drop(columns=['patch','fuel'])
nwk_structure['Year']=pd.DatetimeIndex(nwk_structure['date']).year
nwk_structure = pd.merge(nwk_structure,dst,how='inner',left_on=['Year'],right_on=['YEAR']).drop(columns= ['Year','YEAR'])
print('Applying daylight saving to network...')
nwk_structure['AEDT_Flag'] = nwk_structure.progress_apply(flag_DST, axis = 1)
nwk_structure.drop(columns = ['DST','DST_STARTDATE','DST_ENDDATE'],inplace=True)
nwk_structure = pd.merge(nwk_structure,aus_holiday_table,how='left',left_on=['date','state'],right_on=['date','state'])
nwk_structure['PH_Flag'].fillna(False,inplace=True)
nwk_structure['weekend'] = nwk_structure['date'].dt.day_name().isin(['Saturday', 'Sunday'])

print("Completed column preparation for network timeband application...")
print('Applying date to network...')
nwk_structure['date_applies'] = nwk_structure.progress_apply(date_applies, axis = 1)
nwk_structure = nwk_structure[(nwk_structure['date_applies'])]
print('Applying weekday to network...')
nwk_structure['weekday_applies'] = nwk_structure.progress_apply(weekday_applies, axis = 1)			  
nwk_structure = nwk_structure[(nwk_structure['weekday_applies'])]
print('Applying time/hour to network...')
nwk_structure['time_applies'] = nwk_structure.progress_apply(time_applies, axis = 1)	
print('Length of network structure after all joins: ',len(nwk_structure))
nwk_structure = nwk_structure[(nwk_structure['time_applies'])]
print('Applying component group to network...')
nwk_structure['component_group'] = nwk_structure.progress_apply(network_component_group,axis =1) 
print('Length of network structure filtered: ',len(nwk_structure))
nwk_structure.drop(columns = ['Patch','class','NetworkType','timeband','date_from','date_to',
                                'time_from','time_to','weekday','AEDT_Flag','PH_Flag','weekend',
                                'holiday_as_weekend','date_applies','weekday_applies','time_applies'],inplace=True)

print("Completed network structure... ", len(nwk_structure)," rows")
print("Retail structure for selected registers' tariffs, top 4 rows:")
print(ret_structure.head(4))
print("Network structure for selected registers' tariffs, top 4 rows:")
print(nwk_structure.head(4))

print('Making unique and saving CSV retail...')
ret_structure.drop_duplicates(subset=['RetailTariff','retail_component','date','hour']).to_csv('D:/Temp/retail_structure.csv',header=True, index=False)
print('Making unique and saving CSV retail...')
nwk_structure.drop_duplicates(subset=['NetworkTariff','network_component','date','hour']).to_csv('D:/Temp/network_structure.csv',header=True, index=False)

print("************ Completed creation of network and retail tariff structures at hourly level *************")