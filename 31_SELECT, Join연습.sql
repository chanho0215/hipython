/*
SELECT * FROM 고객;
select * from 사원;
*/
select * -- 고객번호, 고객회사명 
from 고객;
SELECT 고객번호
,담당자명
,마일리지 as 포인트
,고객회사명 AS 이름
from 고객;
select  이름 AS 직원명
, 주소
, 직위 
from 사원
WHERE 직위 = '사원'
ORDER BY 직원명 DESC
LIMIT 10;

SELECT 제품명
, format(단가, 0)
, format(재고 , 0) AS "구매 가능 수량!!" 
, format(단가*재고 , 0) AS "주문가능금액"
FROM  제품
WHERE 단가*재고 >= 100000
ORDER BY 재고
LIMIT 10;

SELECT 제품명
, 재고
FROM 제품
WHERE 단가*재고 >100000
ORDER BY 재고 DESC
LIMIT 10;

SELECT 제품번호
, FORMAT (단가, 0) AS 단가
, 주문수량
, FORMAT(단가*주문수량*(1- 할인율 ) , 0) AS "주문금액"
, 할인율
, FORMAT(단가*주문수량*할인율, 0) AS "할인금액"
FROM 주문세부
ORDER BY 단가*주문수량*할인율 DESC
Limit 10;

SELECT 고객번호
, 담당자명
, 고객회사명
, format(마일리지,0) AS 포인트
, format(마일리지 * 1.2 , 0) AS "20%인상된 마일리지"
FROM 고객
ORDER BY 마일리지*1.2 DESC
limit 10;

SELECT 고객번호
, 담당자명
, 마일리지
FROM 고객
WHERE 마일리지 >= 100000
ORDER BY 마일리지 DESC;

SELECT 이름
, 입사일
FROM 사원
WHERE 직위 = '사원'
ORDER BY 이름
LIMIT 3;


SELECT 제품명
, 재고
FROM 제품
WHERE 단가*재고 > 100000
ORDER BY 2 DESC
limit 7;

SELECT *
FROM 고객
WHERE 마일리지 >= 30000
ORDER BY 마일리지 DESC
LIMIT 3;

SELECT *
FROM 고객
WHERE 마일리지 >= 10000
ORDER BY 마일리지 DESC
LIMIT 6;

SELECT DISTINCT 도시
FROM 고객;

SELECT 23 + 5 AS 더히기
, 23 - 5 AS 빼기
, 23 * 5 AS 곱하기
, 23 / 5 AS 실수나누기
, 23 DIV 5 AS 정수나누기
, 23 % 5 AS 나머지1
, 23 MOD 5 AS 나머지2;

SELECT '오늘의 고객은', CURRENT_DATE, 담당자명
FROM 고객;

SELECT 23 >= 5
, 23 <= 5
, 23 > 23
, 23 < 23
, 23 = 23
, 23 != 23
, 23 <> 23;

SELECT *
FROM 고객
WHERE 담당자직위 <> '대표 이사';

SELECT *
FROM 고객
WHERE 담당자직위 = '대표 이사';

SELECT *
FROM 주문
WHERE 주문일 < '2021-01-01';

SELECT *
FROM 고객
WHERE 도시 = '부산광역시'
AND 마일리지 < 1000;


SELECT *
FROM 고객
WHERE 도시 = '서울특별시'
AND 마일리지 >= 5000;

SELECT *
FROM 고객
WHERE 도시 = '서울특별시'
OR 마일리지 >= 10000;

SELECT *
FROM 고객
WHERE 도시 <> '서울특별시';

SELECT *
FROM 고객
WHERE 도시 <> '서울특별시'
AND 마일리지 >= 5000;

SELECT *
FROM 고객
WHERE 도시 = '서울특별시'
OR 도시 = '부산광역시';


SELECT 고객번호
, 담당자명
, 마일리지
, 도시
FROM 고객
WHERE 도시 = '부산광역시'
UNION
SELECT 고객번호
, 담당자명
, 마일리지
, 도시
FROM 고객
WHERE 마일리지 < 1000
ORDER BY 1;

SELECT 고객번호
, 담당자명
, 마일리지
, 도시
FROM 고객
WHERE 도시 = '부산광역시'
UNION ALL
SELECT 고객번호
, 담당자명
, 마일리지
, 도시
FROM 고객
WHERE 마일리지 < 1000
ORDER BY 1;


SELECT *
FROM 주문세부
WHERE 단가 >= 5000
UNION ALL
SELECT *
FROM 주문세부
WHERE 할인율 >= 0.5
ORDER BY 2;

SELECT 도시
FROM 사원
UNION
SELECT 도시
FROM 고객
;

SELECT *
FROM 고객
WHERE 지역 = ""
ORDER BY 도시;

SELECT DISTINCT 지역 FROM 고객;

SELECT * FROM 고객 ORDER BY 지역 = '' DESC, 도시;

SELECT 고객번호
, 담당자명
, 담당자직위
FROM 고객
WHERE 담당자직위 = '영업 과장'
OR 담당자직위 = '마케팅 과장';

SELECT 고객번호
, 담당자명
, 담당자직위
FROM 고객
WHERE 담당자직위 IN ('영업 과장', '마케팅 과장');

SELECT 담당자명
, 마일리지
FROM 고객
WHERE 마일리지 >= 100000
AND 마일리지 <= 200000;

SELECT 담당자명
, 마일리지
FROM 고객
WHERE 마일리지 BETWEEN 100000 AND 200000;

SELECT *
FROM 사원
WHERE 부서번호 IN ('A1', 'A2')
ORDER BY 부서번호; 

SELECT *
FROM 주문
WHERE 주문일 BETWEEN '2020-06-01' AND '2020-06-11'
ORDER BY 주문일;

SELECT *
FROM 고객
WHERE 고객번호 LIKE 'C%';

SELECT *
FROM 고객
WHERE 고객번호 LIKE '__C__';

SELECT *
FROM 고객
WHERE 고객번호 LIKE '____C';

SELECT *
FROM 고객
WHERE 고객번호 LIKE '%C';

SELECT *
FROM 고객
WHERE 도시 LIKE '%광역시'
AND (고객번호 LIKE '_C___' OR 고객번호 LIKE '__C__');

SELECT FIELD('SQL', 'SQL', 'JAVA', 'C');

SELECT ELT(2, 'SQL', 'JAVA', 'C');

SELECT REPEAT('*', 5);

SELECT REPLACE('010.1234.5678', '.', '-');

SELECT REVERSE('ABCDEF');

SELECT CEILING(123.56)
, FLOOR(123.56)
, ROUND(123.56)
, ROUND(123.56, 1)
, TRUNCATE(123.56, 1);

SELECT ABS(-120)
, ABS(120)
, SIGN(-120)
, SIGn(120);

SELECT NOW()
, SYSDATE()
, CURDATE()
, CURTIME();

SELECT NOW() AS 'START', SLEEP(2), NOW() as "END";







SELECT SYSDATE() AS "START", SLEEP(2),SYSDATE() as "END";


SELECT IF(12500 * 450 > 5000000, '초과달성', '미달성');

SELECT 고객번호, IF(마일리지 > 1000, 'VIP', 'GOLD') AS 등급
FROM 고객;

SELECT 주문번호, IF(단가*주문수량>50000, '안전배송', '일반배송') AS 배송방법
FROM 주문세부;

SELECT 주문번호
,단가
,주문수량
, 단가 * 주문수량 AS 주문금액
, CASE WHEN 단가 * 주문수량 >= 5000000 THEN '초과달성'
	   WHEN 단가 * 주문수량 >= 4000000 THEN '달성'
	   ELSE '미달성'
	   END AS 달성여부
FROM 주문세부;


SELECT 고객번호
, 마일리지
, CASE WHEN 마일리지 >= 100000 THEN 'VIP'
	   WHEN 마일리지 >= 50000  THEN 'GOLD'
       WHEN 마일리지 >= 10000  THEN 'SILVER'
       ELSE 'BRONZE' 
       END AS 등급
FROM 고객;

SELECT * FROM 부서;


SELECT 사원번호
, 이름
, 영문이름
, 직위
, 부서번호
, CASE 
  WHEN 부서번호 = 'A1' THEN '영업부'
  WHEN 부서번호 = 'A2' THEN '기획부'
  WHEN 부서번호 = 'A3' THEN '개발부'
  WHEN 부서번호 = 'A4' THEN '홍보부'
  ELSE '기타'
END AS 부서명
FROM 사원;

SELECT 사원번호, 이름, 영문이름, 직위, 부서번호,
       CASE
         WHEN 부서번호='A1' THEN '영업부'
         WHEN 부서번호='A2' THEN '기획부'
         WHEN 부서번호='A3' THEN '개발부'
         WHEN 부서번호='A4' THEN '홍보부'
         ELSE '기타'
       END AS 부서명
FROM 사원;


SELECT 주문번호, 주문일, 발송일,
CASE
 WHEN 발송일 IS NULL THEN '배송대기'
 WHEN DATEDIFF(발송일, 주문일) <= 2 THEN '빠른배송'
 ELSE '일반배송'
 END AS 배송상태
FROM 주문;



/*연습1. 고객회사명 앞2글자 '*' 마스킹 처리
 * 연습2. 주문세부 정보중 주문금액, 할인금액, 실제주문금액 출력(1단위에서 버림)
 * 연습3. 전체 사원의 이름, 생일, 만나이, 입사일, 입사일수, 입사500일기념일 출력
 * 연습4. 고객 정보의 도시컬럼을 '대도시', '도시'로 구분하고 마일리지 VVIP, VIP, 일반고객 구분
 * 연습5. 주문테이블의 주문일을 주문년도, 분기, 월, 일, 요일, 한글요일로 출력
 * 연습6. 발송일이 요청일보다 7일 이상 늦은 주문건 출력
 * */

SELECT 고객회사명 FROM 고객;

SELECT CONCAT('**', SUBSTRING(고객회사명, 2)) AS 고객회사명
FROM 고객;

SELECT 단가*주문수량 AS 주문금액
, round(단가 * 주문수량 * 할인율 , 1) AS 할인금액
, round(단가 * 주문수량 * (1-할인율) ,1) AS 실제주문금액
FROM 주문세부;

--  연습3. 전체 사원의 이름, 생일, 만나이, 입사일, 입사일수, 입사500일기념일 출력
SELECT 이름,
       생일,
       TIMESTAMPDIFF(YEAR, 생일, CURDATE()) AS 만나이,
       입사일,
       DATEDIFF(CURDATE(), 입사일) AS 입사일수,
       DATE_ADD(입사일, INTERVAL 500 DAY) AS '입사500일기념일'
FROM 사원;

-- 연습4. 고객 정보의 도시컬럼을 '대도시', '도시'로 구분하고 마일리지 VVIP, VIP, 일반고객 구분
SELECT * from 고객;
SELECT 고객번호
, CASE WHEN 도시 LIKE '%광역시' THEN '대도시'
       WHEN 도시 LIKE '%특별시' THEN '대도시'
       ELSE '도시'
       END AS 도시구분
, CASE WHEN 마일리지 >= 50000 THEN 'VVIP'
       WHEN 마일리지 >= 10000 THEN 'VIP'
       ELSE '일반고객'
       END AS 등급
FROM 고객;

-- 연습5. 주문테이블의 주문일을 주문년도, 분기, 월, 일, 요일, 한글요일로 출력

select YEAR(주문일) AS 주문년도
, QUARTER(주문일) AS 분기
, MONTH(주문일) AS 월
, DAY(주문일) AS 일
, WEEKDAY(주문일) 
from 주문;





SELECT 도시
,COUNT(*)
, COUNT(고객번호)
, COUNT(도시)
, COUNT(DISTINCT 지역)
, SUM(마일리지)
, AVG(마일리지)
, MIN(마일리지)
FROM 고객
GROUP by 도시;

SELECT 담당자직위
,도시
, count(고객번호)
, SUM(마일리지)
, AVG(마일리지)
FROM 고객
GROUP BY 담당자직위, 도시
ORDER BY 1,2;

-- GROUP BY 조건 HAVING
SELECT 도시
, COUNT(고객번호) as 고객수
, AVG(마일리지) as 평균_마일리지
FROM 고객
GROUP BY 도시
HAVING SUM(마일리지) > 1000;

SELECT 도시
, COUNT(고객번호)
, SUM(마일리지) as 마일리지합계
FROM 고객
WHERE 고객번호 like 'T%'
GROUP BY 도시
WITH ROLLUP
HAVING SUM(마일리지) > 1000;

-- 광역시 고객, 담당자 직위별로 최대마일리지, 단, 1만점 이상 레코드만 출력
SELECT 담당자직위
, SUM(마일리지)
, AVG(마일리지)
FROM 고객
WHERE 도시 like '%광역시'
GROUP BY 담당자직위
with ROLLUP
HAVING SUM(마일리지) >= 10000
;

SELECT * FROM 고객;

SELECT 담당자직위
, count(담당자직위)
, 도시
FROM 고객
WHERE 담당자직위 LIKE '마케팅%'
GROUP BY 담당자직위, 도시
WITH ROLLUP;

SELECT 부서.부서번호
,사원.부서번호
,부서명
,이름
FROM 부서 JOIN 사원
on 부서.부서번호 = 사원.부서번호
WHERE 이름 = '배재용';

-- 주문, 고객 INNER JOIN
SELECT 
고객회사명
,주문번호
,주문일
FROM 주문 JOIN 고객
on 주문.고객번호 = 고객.고객번호
WHERE 주문.고객번호 = 'ITCWH';

SELECT 주문번호, 주문.사원번호, 고객번호, 사원.이름
FROM 사원 JOIN 주문
on 사원.사원번호 = 주문.사원번호;

SELECT 고객회사명, 제품명
FROM 고객 JOIN 제품 ;

SELECT *
FROM 마일리지등급;

SELECT 고객.고객회사명, 고객.마일리지, 마일리지등급.등급명
FROM 고객 join 마일리지등급
on 고객.마일리지 between 마일리지등급.하한마일리지 AND 마일리지등급.상한마일리지;

SELECT 사원번호
, 직위
, 사원.부서번호
, 부서명
FROM 사원
INNER JOIN 부서
ON 사원.부서번호 = 부서.부서번호
WHERE 이름 = '이소미';

SELECT 고객.고객번호
, 담당자명
, 고객회사명
, COUNT(*) AS 주문건수
FROM 고객
INNER JOIN 주문
ON 고객.고객번호 = 주문.고객번호
GROUP BY 고객.고객번호
, 담당자명
, 고객회사명
ORDER BY COUNT(*) DESC;


/*연습1. 고객회사명 앞2글자 '*' 마스킹 처리
 * 연습2. 주문세부 정보중 주문금액, 할인금액, 실제주문금액 출력(1단위에서 버림)
 * 연습3. 전체 사원의 이름, 생일, 만나이, 입사일, 입사일수, 입사500일기념일 출력
 * 연습4. 고객 정보의 도시컬럼을 '대도시', '도시'로 구분하고 마일리지 VVIP, VIP, 일반고객 구분
 * 연습5. 주문테이블의 주문일을 주문년도, 분기, 월, 일, 요일, 한글요일로 출력
 * 연습6. 발송일이 요청일보다 7일 이상 늦은 주문건 출력
 * */

SELECT 고객회사명 FROM 고객;

SELECT CONCAT('**', SUBSTRING(고객회사명, 2)) AS 고객회사명
FROM 고객;

SELECT 단가*주문수량 AS 주문금액
, round(단가 * 주문수량 * 할인율 , 1) AS 할인금액
, round(단가 * 주문수량 * (1-할인율) ,1) AS 실제주문금액
FROM 주문세부;

--  연습3. 전체 사원의 이름, 생일, 만나이, 입사일, 입사일수, 입사500일기념일 출력
SELECT 이름,
       생일,
       TIMESTAMPDIFF(YEAR, 생일, CURDATE()) AS 만나이,
       입사일,
       DATEDIFF(CURDATE(), 입사일) AS 입사일수,
       DATE_ADD(입사일, INTERVAL 500 DAY) AS '입사500일기념일'
FROM 사원;

-- 연습4. 고객 정보의 도시컬럼을 '대도시', '도시'로 구분하고 마일리지 VVIP, VIP, 일반고객 구분
SELECT * from 고객;
SELECT 고객번호
, CASE WHEN 도시 LIKE '%광역시' THEN '대도시'
       WHEN 도시 LIKE '%특별시' THEN '대도시'
       ELSE '도시'
       END AS 도시구분
, CASE WHEN 마일리지 >= 50000 THEN 'VVIP'
       WHEN 마일리지 >= 10000 THEN 'VIP'
       ELSE '일반고객'
       END AS 등급
FROM 고객;

-- 연습5. 주문테이블의 주문일을 주문년도, 분기, 월, 일, 요일, 한글요일로 출력

select YEAR(주문일) AS 주문년도
, QUARTER(주문일) AS 분기
, MONTH(주문일) AS 월
, DAY(주문일) AS 일
, DAYNAME(주문일) 
, CASE weekday(주문일)
         WHEN 0 THEN '월'
         WHEN 1 THEN '화'
         WHEN 2 THEN '수'
         WHEN 3 THEN '목'
         WHEN 4 THEN '금'
         WHEN 5 THEN '토'
         WHEN 6 THEN '일'
       END AS 한글요일
from 주문;

-- * 연습6. 발송일이 요청일보다 7일 이상 늦은 주문건 출력
SELECT 주문번호,
       주문일,
       요청일,
       발송일
FROM 주문
WHERE DATEDIFF(발송일, 요청일) >= 7;

-- 연습1. 담당자 직위에 마케팅이 있는 고객의 담당자직위, 도시별 고객수 출력
-- 단, 담당자직위별 고객수와 전체 고객수도 출력

SELECT 담당자직위
, count(담당자직위)
, 도시
FROM 고객
WHERE 담당자직위 LIKE '마케팅%'
GROUP BY 담당자직위, 도시
WITH ROLLUP;

-- 연습2. 제품 주문년도별 주문건수 출력
SELECT YEAR(주문일) AS 주문년도
, COUNT(주문번호) AS 주문건수
FROM 주문
GROUP BY year(주문일)
WITH ROLLUP;

-- 연습3. 주문년도, 분기별 주문건수 합계 출력
SELECT YEAR(주문일) AS 주문년도
, quarter(주문일) AS 주문분기
, COUNT(주문번호) AS 주문건수
FROM 주문
GROUP BY year(주문일), quarter(주문일)
WITH ROLLUP;
-- 연습4. 주문 요청일보다 발송이 늦어진 주문내역이 월별로 몇건인지 요약 조회
-- 주문월 순으로 정렬

SELECT YEAR(요청일) AS 주문년도,
       MONTH(요청일) AS 주문월,
       COUNT(*) AS 지연주문건수
FROM 주문
WHERE 발송일 > 요청일
GROUP BY YEAR(요청일), MONTH(요청일)
ORDER BY 주문년도, 주문월;

-- 연습5. 아이스크림 제품명 별로 재고합 출력
SELECT 제품명
,재고
FROM 제품 
WHERE 제품명 LIKE '%아이스크림';


SELECT 주문번호
, 이름 as 사원명
,주문.사원번호
, 입사일
, 주문일
FROM 사원 join 주문
ON 주문.사원번호 = 사원.사원번호
AND 주문.주문일 >= 사원.입사일;

SELECT 고객회사명
,COUNT(주문.고객번호) as 주문횟수
from 고객 JOIN 주문
ON 고객.고객번호 = 주문.고객번호
GROUP BY 고객회사명
ORDER BY 주문횟수 DESC;

SELECT 고객회사명
, 제품번호
, 담당자명
, 주문일
, format(SUM(단가*주문수량*(1-할인율)), 0) AS 주문금액
FROM 고객 
JOIN 주문 
ON 고객.고객번호 = 주문.고객번호
JOIN 주문세부
ON 주문.주문번호 = 주문세부.주문번호
GROUP BY 고객회사명, 제품번호, 담당자명, 주문일
ORDER BY SUM(단가*주문수량*(1-할인율)) DESC;


SELECT DISTINCT 부서번호
FROM 사원;


SELECT 사원번호, 이름, 부서명
FROM 사원 left JOIN 부서 
on 사원.부서번호 = 부서.부서번호;

SELECT 사원번호, 이름, 부서명
FROM 사원 right JOIN 부서
ON 사원.부서번호 = 부서.부서번호
WHERE 사원번호 is null;

SELECT 고객.고객번호, 주문번호
FROM 고객 left join 주문
on 고객.고객번호 = 주문.고객번호
where 주문.고객번호 is null;
