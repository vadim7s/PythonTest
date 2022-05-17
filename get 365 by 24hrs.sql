with past365( date ) as
		(select GETDATE() 
		union all
		select DATEADD(day,-1,date)
		from past365 where date > DATEADD(day,1,(DATEADD(year,-1,GETDATE())))
)
select cast(a.date as date) as date
--,b.h as hr 
from past365 a
--inner join hours b on 1=1
where month(a.date)<>2 or day(a.date)<>29
order by a.date option (maxrecursion 367)
