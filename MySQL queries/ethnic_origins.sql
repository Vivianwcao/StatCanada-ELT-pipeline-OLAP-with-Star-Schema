ALTER TABLE
    staging_ethnic_origins RENAME COLUMN "statistics" TO stats;

SELECT
    seo.ref_date,
    seo.coordinate,
    count(*)
FROM
    public.staging_ethnic_origins seo
GROUP BY
    seo.ref_date,
    seo.coordinate
HAVING
    count(*) > 1;

--count dot + 1
SELECT
    coordinate,
    length(REPLACE(coordinate, '.', '')) AS dimension_count
FROM
    public.staging_ethnic_origins
LIMIT
    25;

SELECT
    coordinate,
    count(*)
FROM
    public.staging_ethnic_origins
GROUP BY
    coordinate
HAVING
    count(*) > 1;

-- Clean up columns that have trailing spaces (common in StatCan text)
UPDATE
    public.staging_ethnic_origins
SET
    coordinate = TRIM(coordinate);

SELECT
    count(*)
FROM
    ethnic.fact_ethnic_origins;

SELECT
    member_name_en,
    count(*)
FROM
    ethnic.dim_labour_force_characteristics
GROUP BY
    member_name_en
SELECT
    coordinate,
    split_part(coordinate, '.', 1) :: int AS FIRST,
    split_part(coordinate, '.', 2) :: int AS SECOND,
    split_part(coordinate, '.', 3) :: int AS third
FROM
    public.staging_ethnic_origins;