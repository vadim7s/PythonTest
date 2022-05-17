/****** Script for SelectTopNRows command from SSMS  ******/


/* network structure */
select tbc.network_tariff
,tbc.network_component
,t.code as timeband
,t.date_from
,t.date_to
,t.time_from
,t.time_to
,t.weekday 
,s.class, s.Patch,s.KVA,s.HolidayAsWeekend,s.NetworkType,
s.network_component_l1,s.network_component_l2,s.network_component_l3
from pricing.pricing_timebands t
inner join
(SELECT 
network_tariff_patch_id_Code as network_tariff
,tariff_component_Code as network_component
,u.tbs as timeband
FROM AGL_MDS.pricing.pricing_network_tariff_component_timeband
unpivot  (tbs for tb in (tb1_Code,tb2_Code,tb3_Code,tb4_Code,tb5_Code,tb6_Code,tb7_Code,tb8_Code,tb9_Code,tb10_Code)) u
where state='Active' and VersionFlag='Active') tbc
on tbc.timeband=t.code and t.VersionFlag = 'Active' and t.State = 'Active'
inner join
(select c.code as nwk_tariff_component, 
c.network_component_l1,c.network_component_l2,c.network_component_l3,cm.class,
cm.NetworkTariff,cm.Patch,cm.NetworkTariffStructure,cm.KVA,cm.HolidayAsWeekend,cm.NetworkType
from pricing.pricing_network_tariff_components c
inner join (
select Code as NetworkTariff,
netw_tariff_structure_Code as NetworkType,
patch_id_Code as Patch,
network_tariff_id as NetworkTariffStructure,
netw_class_code as class,
netw_holiday_as_weekend as HolidayAsWeekend,
[KVA demand_Code] as KVA,
u.comps as network_component
from AGL_MDS.pricing.pricing_network_tariff 
unpivot(comps for comp in (c1_Code,c2_Code,c3_Code,c4_Code,c5_Code,c6_Code,c7_Code,c8_Code,c9_Code,c10_Code)) u 
where State = 'Active' and VersionFlag = 'Active') cm
on cm.network_component=c.Code
) s
on s.NetworkTariff=tbc.Network_tariff and s.nwk_tariff_component=tbc.network_component





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

