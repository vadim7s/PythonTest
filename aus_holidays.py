import holidays
import pandas as pd
import datetime
year_from = datetime.datetime.now().year - 2
year_to = datetime.datetime.now().year + 1


aus_holiday_table=pd.DataFrame()
for state in ['ACT','VIC','NSW','QLD','WA']:
    holidays_list = [x[0] for x in holidays.Australia(years=[year_from,year_to],prov=state).items()]
    holidays_list = pd.DataFrame(holidays_list)
    holidays_list['state']=state
    aus_holiday_table = pd.concat([aus_holiday_table,holidays_list],0)
aus_holiday_table.rename(columns={aus_holiday_table.columns[0]: 'date'},inplace=True)

aus_holiday_table['date'] = pd.to_datetime(aus_holiday_table['date'], format= '%Y/%m/%d')

#aus_holiday_table['date'] = aus_holiday_table['date'].apply(lambda x: x.date())
print(aus_holiday_table[(aus_holiday_table['state']=='VIC')].head(3))
print(aus_holiday_table.dtypes)

