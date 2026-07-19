import json
from sqlalchemy import create_engine, text
import requests
import logging

# ── Logging ─────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # required for lambda
logging.basicConfig(level=logging.INFO)  # required for local


DB_URL = "postgresql://postgres:1234@localhost:5432/data_cleaning"
engine = create_engine(DB_URL, pool_size=5, max_overflow=10)


def post_request(url, payload):
    try:
        res = requests.post(url, json=payload, timeout=5)

        # 1. Triggers HTTPError if status is 4xx or 5xx
        res.raise_for_status()

        # 2. May trigger JSONDecodeError if server returns bad JSON
        data = res.json()
        return data

    except requests.exceptions.JSONDecodeError:
        #  sub-class of HTTPError, placed first in order
        # Handle cases where the server returned HTML or plain text instead of JSON
        logger.error("Server response was not valid JSON.")
        return None

    except requests.exceptions.HTTPError:
        # Handle 404, 500, 403, etc. (triggered by raise_for_status)
        logger.error("HTTP error occurred")
        return None


def generate_on_conflict_query_list(table_info: dict):
    cols = table_info.get("additional_cols")
    if not cols:
        return []
    return [f"{c} = excluded.{c}" for c in cols]


def filter_query_mapper(query, complete_mapper: dict):
    required_keys = set(query.compile().params.keys())
    return {k: v for k, v in complete_mapper.items() if k in required_keys}


def write_into_dimension_tables(dimension: dict):
    """Handle one dimension table"""

    dimension_table_position_mapper = {
        1: {
            "table_name": "dim_geography",
            "additional_cols": ["parent_member_id", "geo_level", "classification_code"],
        },
        2: {
            "table_name": "dim_labour_force_characteristics",
            "additional_cols": ["parent_member_id"],
        },
        3: {"table_name": "dim_gender", "additional_cols": ["parent_member_id"]},
        4: {"table_name": "dim_age_group"},
        5: {"table_name": "dim_statistics"},
        6: {"table_name": "dim_data_type"},
    }

    table_info = dimension_table_position_mapper.get(dimension["dimensionPositionId"])

    if not table_info:
        logger.warning("dimension table not in Cube meta data. Exit.")
        return None

    members = dimension["member"]
    table_name = table_info["table_name"]

    query = text(f"""
        insert into ethnic.{table_name} (
                member_id, 
                member_name_en,  
                {", ".join(table_info.get("additional_cols", []))}
            )
        values(
                :member_id,
                :member_name_en,
                :{", :".join(table_info.get("additional_cols", []))}
            )
        on conflict (member_id) do update
        set member_name_en = excluded.member_name_en,
            {", ".join(generate_on_conflict_query_list(table_info))}
    """)

    with engine.begin() as connection:
        for m in members:
            complete_mapper = {
                "member_id": m["memberId"],
                "parent_member_id": m["parentMemberId"],
                "member_name_en": m["memberNameEn"],
                "geo_level": m["geoLevel"],
                "classification_code": m["classificationCode"],
            }
            safe_mapper = filter_query_mapper(query, complete_mapper)

            connection.execute(query, safe_mapper)

    logger.info(f"Complete filling dimension table - {table_name}")


def main():
    try:
        url = "https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata"
        payload = [{"productId": 14100287}]

        # get CubeMetaData json from API
        data = post_request(url, payload)
        logger.info(data)

        if not data:
            logger.warning("Failed to get Cube meta data")
            return None

        dimension = data[0]["object"]["dimension"]

        # d is one dimension table
        for d in dimension:
            write_into_dimension_tables(d)

    except Exception:
        logger.exception("Failed")


if __name__ == "__main__":
    main()
