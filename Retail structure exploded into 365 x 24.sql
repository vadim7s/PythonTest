/****** create 365 days over 24 hrs for all timebands  for retail tariffs ******/
/****** NOTE - INCOMPLETE - yet to apply timeband rules and weekend/weekday logic   *****/

with past365(date ) as
		(select GETDATE() 
		union all
		select DATEADD(day,-1,date)
		from past365 where date > DATEADD(day,1,(DATEADD(year,-1,GETDATE())))),
	hours(h) as (select 0 as h union all select h+1 from hours where h<23)
select --top (1000)
cast(a.date as date) as date,
format(b.h,'0#') as hr,
x.*
from past365 a
inner join hours b on 1=1 --at this point 365 is exploded by 24
inner join (
/* retail component structure at timeband level */
select tbc.retail_tariff
,tbc.retail_component,t.code as timeband
,t.date_from,t.date_to,t.time_from,t.time_to,t.weekday,
s.class, s.DefaultNetworkTariff,s.Patch,s.ret_tariff_comp_description,
s.retail_component_l1,s.retail_component_l2,s.retail_component_l3
from pricing.pricing_timebands t 
inner join 
(SELECT retail_tariff_class_patch_id_Code as retail_tariff
,tariff_component_Code as retail_component,u.tbs as timeband 
FROM AGL_MDS.pricing.pricing_retail_tariff_component_timeband 
unpivot  (tbs for tb in (tb1_Code,tb2_Code,tb3_Code,tb4_Code,tb5_Code,tb6_Code,tb7_Code,tb8_Code,tb9_Code,tb10_Code)) u 
where state='Active' and VersionFlag='Active') tbc 
on tbc.timeband=t.code 

inner join (
select c.Name as ret_tariff_comp_description, c.code as ret_tariff_component, 
c.retail_component_l1,c.retail_component_l2,c.retail_component_l3,cm.class,
cm.Retail_Tariff_Code,cm.Patch,cm.RetailTariffStructure,cm.DefaultNetworkTariff
from pricing.pricing_retail_tariff_components c
inner join (
select Code as Retail_Tariff_Code,
patch_id_Code as Patch,
retail_tariff_id as RetailTariffStructure,
Class_code as class,
retail_tariff_type_Code as RetailTariffType,
default_network_tariff_Code as DefaultNetworkTariff,
u.comps as retail_component
from AGL_MDS.pricing.pricing_retail_tariff 
unpivot(comps for comp in (c1_Code,c2_Code,c3_Code,c4_Code,c5_Code,c6_Code,c7_Code,c8_Code,c9_Code,c10_Code)) u 
where State = 'Active' and VersionFlag = 'Active') cm
on cm.retail_component=c.Code
) s
on s.Retail_Tariff_Code=tbc.retail_tariff and s.ret_tariff_component=tbc.retail_component
where t.VersionFlag = 'Active' and t.State = 'Active'
) x on 1=1 
where (month(a.date)<>2 or day(a.date)<>29) -- excl Feb 29
and x.retail_tariff='5 Day TOD - RESI (SOLARISP)'
option (maxrecursion 365)


