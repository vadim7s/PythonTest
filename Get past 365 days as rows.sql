
CREATE VIEW digits AS
  SELECT 0 AS digit UNION ALL
  SELECT 1 UNION ALL
  SELECT 2 UNION ALL
  SELECT 3 UNION ALL
  SELECT 4 UNION ALL
  SELECT 5 UNION ALL
  SELECT 6 UNION ALL
  SELECT 7 UNION ALL
  SELECT 8 UNION ALL
  SELECT 9

GO
CREATE VIEW numbers AS
  SELECT
    ones.digit + tens.digit * 10 + hundreds.digit * 100 + thousands.digit * 1000 AS number
  FROM
    digits as ones,
    digits as tens,
    digits as hundreds,
    digits as thousands

GO

CREATE VIEW dates AS
  SELECT
    dateadd(day, -number, getdate()) AS date
  FROM
    numbers
GO
SELECT
  cast(date as date) as Date
FROM
  dates
WHERE
  date > dateadd(day, -365, getdate())
ORDER BY
  date;

drop view dates;
GO

drop view digits;
GO

drop view numbers;
GO