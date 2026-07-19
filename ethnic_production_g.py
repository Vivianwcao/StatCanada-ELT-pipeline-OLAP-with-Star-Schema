import requests
from sqlalchemy import create_engine, text
import logging

# ── Logging ─────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # required for lambda
logging.basicConfig(level=logging.INFO)  # required for local

# 1. Instantiate the Engine ONCE globally/centrally
DB_URL = "postgresql://postgres:1234@localhost:5432/data_cleaning"
engine = create_engine(DB_URL, pool_size=5, max_overflow=10)

# 2. Hardcoded, explicit SQL queries. Highly readable, easy to test.
DIMENSION_QUERIES = {
    1: text("""
        INSERT INTO ethnic.dim_geography (member_id, parent_member_id, member_name_en, classification_code, geo_level)
        VALUES (:member_id, :parent_member_id, :member_name_en, :classification_code, :geo_level)
        ON CONFLICT (member_id) DO UPDATE SET
            member_name_en = EXCLUDED.member_name_en,
            parent_member_id = EXCLUDED.parent_member_id,
            geo_level = EXCLUDED.geo_level,
            classification_code = EXCLUDED.classification_code;
    """),
    2: text("""
        INSERT INTO ethnic.dim_labour_force_characteristics (member_id, parent_member_id, member_name_en)
        VALUES (:member_id, :parent_member_id, :member_name_en)
        ON CONFLICT (member_id) DO UPDATE SET
            member_name_en = EXCLUDED.member_name_en,
            parent_member_id = EXCLUDED.parent_member_id;
    """),
    3: text("""
        INSERT INTO ethnic.dim_gender (member_id, parent_member_id, member_name_en)
        VALUES (:member_id, :parent_member_id, :member_name_en)
        ON CONFLICT (member_id) DO UPDATE SET
            member_name_en = EXCLUDED.member_name_en,
            parent_member_id = EXCLUDED.parent_member_id;
    """),
    4: text("""
        INSERT INTO ethnic.dim_age_group (member_id, member_name_en)
        VALUES (:member_id, :member_name_en)
        ON CONFLICT (member_id) DO UPDATE SET member_name_en = EXCLUDED.member_name_en;
    """),
    5: text("""
        INSERT INTO ethnic.dim_statistics (member_id, member_name_en)
        VALUES (:member_id, :member_name_en)
        ON CONFLICT (member_id) DO UPDATE SET member_name_en = EXCLUDED.member_name_en;
    """),
    6: text("""
        INSERT INTO ethnic.dim_data_type (member_id, member_name_en)
        VALUES (:member_id, :member_name_en)
        ON CONFLICT (member_id) DO UPDATE SET member_name_en = EXCLUDED.member_name_en;
    """),
}


def populate_dimension(dimension_data):
    position_id = dimension_data["dimensionPositionId"]
    query = DIMENSION_QUERIES.get(position_id)

    if query is None:
        logger.warning(
            f"No query mapped for dimension position {position_id}. Skipping."
        )
        return

    logger.info(f"Processing dimension position {position_id}...")

    # Share the core connection pool efficiently
    with engine.begin() as connection:
        for member in dimension_data["member"]:
            # Explicit parameters mapped safely without complex filtering tricks
            params = {
                "member_id": member["memberId"],
                "member_name_en": member["memberNameEn"],
                "parent_member_id": member.get("parentMemberId"),
                "classification_code": member.get("classificationCode"),
                "geo_level": member.get("geoLevel"),
            }
            connection.execute(query, params)


def main():
    url = "https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata"
    payload = [{"productId": 14100287}]

    try:
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        data = res.json()

        dimensions = data[0]["object"]["dimension"]
        for d in dimensions:
            populate_dimension(d)

        logger.info("All dimension tables synchronized successfully.")

    except Exception:
        logger.exception("Pipeline Execution Failed")


if __name__ == "__main__":
    main()
