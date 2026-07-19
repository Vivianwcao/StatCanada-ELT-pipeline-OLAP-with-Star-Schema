DROP SCHEMA IF EXISTS ethnic CASCADE;

CREATE schema ethnic;

CREATE TABLE ethnic.dim_geography(
    member_id int PRIMARY KEY,
    parent_member_id int REFERENCES ethnic.dim_geography(member_id),
    member_name_en varchar(255) NOT NULL,
    classification_code varchar(100),
    geo_level int
);

CREATE TABLE ethnic.dim_gender (
    member_id int PRIMARY KEY,
    parent_member_id int REFERENCES ethnic.dim_gender(member_id),
    member_name_en varchar(50) NOT NULL
);

CREATE TABLE ethnic.dim_labour_force_characteristics (
    member_id int PRIMARY KEY,
    parent_member_id int REFERENCES ethnic.dim_labour_force_characteristics (member_id),
    member_name_en varchar(100) NOT NULL
);

ALTER TABLE
    ethnic.dim_labour_force_characteristics RENAME parent_memeber_id TO parent_member_id;

CREATE TABLE ethnic.dim_age_group (
    member_id int PRIMARY KEY,
    member_name_en varchar(100) NOT NULL
);

CREATE TABLE ethnic.dim_statistics (
    member_id int PRIMARY KEY,
    member_name_en varchar(150) NOT NULL
);

CREATE TABLE ethnic.dim_data_type (
    member_id int PRIMARY KEY,
    member_name_en varchar(100) NOT NULL
);

CREATE TABLE ethnic.fact_ethnic_origins(
    fact_id int generated always AS identity PRIMARY KEY,
    ref_date varchar(50) NOT NULL,
    uom varchar(100),
    uom_id int,
    scalar_factor varchar(100),
    scalar_id int,
    value float,
    geography_id int REFERENCES ethnic.dim_geography(member_id),
    gender_id int REFERENCES ethnic.dim_gender(member_id),
    labour_characteristics_id int REFERENCES ethnic.dim_labour_force_characteristics(member_id),
    age_group_id int REFERENCES ethnic.dim_age_group(member_id),
    statistics_id int REFERENCES ethnic.dim_statistics(member_id),
    data_type_id int REFERENCES ethnic.dim_data_type(member_id),
    CONSTRAINT unique_fact_intersection UNIQUE (
        ref_date,
        geography_id,
        gender_id,
        labour_characteristics_id,
        age_group_id,
        statistics_id,
        data_type_id
    )
);

INSERT INTO
    ethnic.fact_ethnic_origins(
        ref_date,
        uom,
        uom_id,
        scalar_factor,
        scalar_id,
        value,
        geography_id,
        labour_characteristics_id,
        gender_id,
        age_group_id,
        statistics_id,
        data_type_id
    )
SELECT
    ref_date,
    uom,
    uom_id,
    scalar_factor,
    scalar_id,
    value,
    split_part(coordinate, '.', 1) :: INT AS geography_id,
    split_part(coordinate, '.', 2) :: INT AS labour_characteristics_id,
    split_part(coordinate, '.', 3) :: INT AS gender_id,
    split_part(coordinate, '.', 4) :: INT AS age_group_id,
    split_part(coordinate, '.', 5) :: INT AS statistics_id,
    split_part(coordinate, '.', 6) :: INT AS data_type_id
FROM
    public.staging_ethnic_origins
WHERE
    coordinate IS NOT NULL
    AND value IS NOT NULL --	Just silently skip that duplicate row and move on to the next one.
    ON conflict ON CONSTRAINT unique_fact_intersection DO nothing;