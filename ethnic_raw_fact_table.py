import io
import zipfile
import requests
import pandas as pd
from sqlalchemy import create_engine

# Canada Statistic ProductId is 14100287

# 1. Target URL from your API response
zip_url = "https://www150.statcan.gc.ca/n1/tbl/csv/14100287-eng.zip"

print("Starting download...")
# Stream the download to establish a steady network pipe
response = requests.get(zip_url, stream=True)

if response.status_code == 200:
    print("Download complete. Processing ZIP file in memory...")

    # 2. Store the compressed ZIP entirely in RAM using BytesIO.
    # CRITICAL CHECK: Bypassing local disk I/O makes this significantly faster and cloud-friendly (perfect for AWS Lambda storage limits).
    zip_buffer = io.BytesIO(response.content)

    with zipfile.ZipFile(zip_buffer) as z:
        # StatCan ZIPs contain a main CSV file and a MetaData text file.
        # Find the main dataset CSV dynamically.
        csv_filename = [name for name in z.namelist() if name.endswith(".csv")][0]
        print(f"Found CSV file inside ZIP: {csv_filename}")

        # 3. Establish your PostgreSQL Connection (Using SQLAlchemy)
        DB_USER = "postgres"
        DB_PASS = "1234"
        DB_HOST = "localhost"
        DB_PORT = "5432"
        DB_NAME = "data_cleaning"

        engine = create_engine(
            f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

        # 4. Stream the CSV in controlled CHUNKS
        # CRITICAL CHECK: Pandas expands text objects in RAM by 3x-5x.
        # Setting 'chunksize' processes only 50,000 rows at a time, keeping RAM stable.
        chunk_size = 50000
        target_table = "staging_ethnic_origins"

        print(f"Streaming data into PostgreSQL '{target_table}' in chunks...")

        # Open the raw CSV stream directly inside the compressed ZIP structure
        with z.open(csv_filename) as csv_file:
            for i, chunk in enumerate(
                pd.read_csv(csv_file, chunksize=chunk_size, low_memory=False)
            ):
                # StatCan column names contain spaces and punctuation,
                # Clean them on the fly to lowercase snake_case here.
                chunk.columns = [
                    col.strip()
                    .lower()
                    .replace(" ", "_")
                    .replace("(", "")
                    .replace(")", "")
                    .replace("-", "_")
                    for col in chunk.columns
                ]

                # First chunk creates/replaces the table schema.
                # Subsequent loops append rows incrementally.
                if i == 0:
                    chunk.to_sql(
                        target_table, con=engine, if_exists="replace", index=False
                    )
                else:
                    chunk.to_sql(
                        target_table, con=engine, if_exists="append", index=False
                    )

                print(f"Successfully loaded chunk {i + 1} ({len(chunk)} rows added).")

    print("Data Pipeline Execution Successful! Staging table populated.")
else:
    print(f"Download failed. HTTP Status Code: {response.status_code}")
