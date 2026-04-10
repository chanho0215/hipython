USE wntrade;

show tables;
select * from wntrade.고객;


SELECT 사원번호, 이름, 부서명
FROM 사원 LEFT JOIN 부서
ON 사원.부서번호 = 부서.부서번호;

SELECT  A.고객회사명, A.담당자명, A.마일리지
FROM 고객 A
LEFT JOIN 고객 B
ON A.마일리지 < B.마일리지
WHERE B.고객번호 IS NULL;

Select 고객번호
, 고객회사명
, 담당자명
, 마일리지
, 등급명
FROM 고객
, 마일리지등급
WHERE 마일리지 Between 하한마일리지 AND 상한마일리지
AND 담당자명 = '이은광';

Select 고객번호
, 고객회사명
, 담당자명
, 마일리지
, 등급명
FROM 고객
Inner Join 마일리지등급
on 마일리지 >= 하한마일리지 
AND 마일리지 <= 상한마일리지
WHere 담당자명 = '이은광';

Select 부서명
,사원.*
From 사원
RIght Outer Join 부서
ON 사원.부서번호 = 부서.부서번호
WHERE 사원.부서번호 IS NULL;

Select 부서.부서번호, 부서명, 사원.이름
FROM 사원
RIGHT Join 부서
on 사원.부서번호 = 부서.부서번호;

SELECT 이름
, 부서.*
FROM 사원
RIGHT JOIN 부서
ON 사원.부서번호 = 부서.부서번호
WHERE 부서.부서번호 is null;

Select 고객.고객번호, 고객회사명, 담당자명,  주문번호
FROM 주문
RIGHT JOIN 고객
ON 주문.고객번호 = 고객.고객번호
WHERE 주문.주문번호 is null;


SELECT 사원.사원번호
 , 사원.이름
 ,상사.사원번호 AS '상사의 사원번호'
 ,상사.이름 AS '상사의 이름'
FROM 사원
LEft Join 사원 AS 상사
ON 사원.상사번호 = 상사.사원번호
WHERE 사원.상사번호 = '';

SELECT 고객번호
, 고객회사명
, 담당자명
, 마일리지
FROM 고객
WHERE 마일리지 = (SELECT MAX(마일리지)
from 고객
);

-- 주문번호 = 'h0250'인 고객회사명, 담당자명
SELECT 고객.고객회사명, 고객.담당자명
FROM 고객 join 주문 on 고객.고객번호 = 주문.고객번호
WHERE 주문번호 = 'h0250';

-- 서브쿼리로
SELECT 고객.고객회사명, 고객.담당자명
FROM 고객
WHERE 고객.고객번호 = (SELECT 주문.고객번호
						FROM 주문
                        WHERE 주문번호 = 'h0250');
                        
SELECT 담당자명
, 고객회사명
, 마일리지
FROM 고객
WHERE 고객.마일리지 > (SELECT Min(마일리지)
						FROM 고객
						WHERE 도시 = '부산광역시');
                        
SELECT COUNT(*) AS 주문건수
FROM 주문
WHERE 고객번호 IN (SELECT 고객번호 
FROM 고객 
WHERE 도시 = '부산광역시');


SELECT 담당자명
, 고객회사명
, 마일리지
FROM 고객
WHERE 마일리지 > ANY (SELECT 마일리지
					  FROM 고객
                      WHERE 도시 = '부산광역시'
                      );
                      
SELECT 담당자명
, 고객회사명
, 마일리지
FROM 고객
WHERE 마일리지 > ALL (Select AVG(마일리지)
						FROM 고객
                        GROUP BY 지역
                        );
                        
SELECT 고객번호
, 고객회사명
FROM 고객
WHERE EXISTS (select *
			  FROM 주문
              WHERE 고객번호 = 고객.고객번호
              );
	
SELECT 고객번호
	, 고객회사명
FROM 고객
WHERE 고객번호 IN (SELECT DISTINCT 고객번호
					FROM 주문
                    );

SELECT 도시
, AVG(마일리지)  AS 평균마일리지
FROM 고객
GROUP BY 도시
HAVING AVG(마일리지) > (SELECT AVG (마일리지)
						FROM 고객
                        );
                        
                        
SELECT 담당자명
, 고객회사명
, 마일리지
, 고객.도시
, 도시_평균마일리지
, 도시_평균마일리지 - 마일리지 AS 차이
FROM 고객
, (SELECT 도시
	, AVG(마일리지) AS 도시_평균마일리지
    FROM 고객
    GROUP BY 도시
) AS 도시별요약
WHERE 고객.도시 = 도시별요약.도시;

SELECT 고객번호
,담당자명
,(SELECT MAX(주문일)
FROM 주문
WHERE 주문.고객번호 = 고객.고객번호
) AS 최종주문일
FROM 고객;

SELECT 사원번호
, 이름
, 상사번호
, (SELECT 이름
FROM 사원 AS 상사
WHERE 상사.사원번호 = 사원.상사번호
) AS 상사이름
FROM 사원;