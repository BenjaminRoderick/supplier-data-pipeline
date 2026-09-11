import numpy as np
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

from pathlib import Path

def import_clean_data(input_folder='data', supplier_filename='supplier_feed.csv', metadata_filename='product_metadata.csv'):
    """
    given only the supplier_feed needs cleaning, product_metadata is just loaded into a pd.dataframe

    modifications to supplier_feed:
    - entry_date: convert mixed date formats to datetime
    - stock_level: convert to int, default string and NaN to 0
    - cost_price: remove $ sign and convert to float, then backfill missing values for each part_id
    """
    parent_path = Path(__file__).parent.parent
    input_folder = parent_path / input_folder

    supplier_feed = pd.read_csv(Path(input_folder) / supplier_filename)
    supplier_feed['entry_date'] = pd.to_datetime(supplier_feed['entry_date'], errors='coerce', format='mixed')
    supplier_feed = supplier_feed.sort_values(by=['part_id', 'entry_date'], ascending=[True, False])
    supplier_feed['stock_level'] = pd.to_numeric(supplier_feed['stock_level'], errors='coerce').fillna(0).astype(int)
    supplier_feed['cost_price'] = supplier_feed['cost_price'].astype(str).str.replace(r'[$]', '', regex=True).astype('float')
    supplier_feed['cost_price'] = supplier_feed.groupby('part_id')['cost_price'].bfill()

    product_metadata = pd.read_csv(Path(input_folder) / metadata_filename)

    return supplier_feed, product_metadata

def create_database(input_folder='data', supplier_filename='supplier_feed.csv', metadata_filename='product_metadata.csv'):
    """
    """
    supplier_feed, product_metadata = import_clean_data(input_folder, supplier_filename, metadata_filename)

    with sqlite3.connect(Path(input_folder) / 'supplier_data.db') as connection:
        cursor = connection.cursor()

        def table_exists(name):
            result = cursor.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name = ?
                """,
                (name,)
            ).fetchone()

            return result is not None

        if table_exists('supplier_feed'):
            cursor.execute("DROP TABLE supplier_feed")
            print("Dropped existing table: supplier_feed")
        if table_exists('product_metadata'):
            cursor.execute("DROP TABLE product_metadata")
            print("Dropped existing table: product_metadata")

        cursor.execute(
            """
                CREATE TABLE supplier_feed (
                    part_id TEXT NOT NULL,
                    stock_level INTEGER,
                    cost_price REAL,
                    entry_date TEXT
                )
            """
        )
        cursor.execute(
            """
                CREATE TABLE product_metadata (
                    part_id TEXT PRIMARY KEY,
                    part_name TEXT,
                    category TEXT
                )
            """
        )
        

        supplier_feed.to_sql('supplier_feed', connection, if_exists='append', index=False)
        product_metadata.to_sql('product_metadata', connection, if_exists='append', index=False)


if __name__ == '__main__':
    input_folder = 'data'
    create_database(input_folder=input_folder)


    with sqlite3.connect(Path(input_folder) / 'supplier_data.db') as connection:
        cursor = connection.cursor()

        # find average cost_price for each category
        cursor.execute(
            """
                WITH latest_entries AS (
                    SELECT part_id, stock_level, cost_price, MAX(entry_date) AS latest_entry_date
                    FROM supplier_feed
                    GROUP BY part_id
                )
                SELECT m.category, AVG(s.cost_price) AS avg_cost_price
                FROM latest_entries s
                JOIN product_metadata m ON s.part_id = m.part_id
                GROUP BY m.category
                ORDER BY avg_cost_price DESC
            """
        )
        avg_cost_prices = cursor.fetchall()

        # find the top 5 part_ids with the highest stock_level in the most recent entry_date
        cursor.execute(
            """
                WITH latest_entries AS (
                    SELECT part_id, stock_level, cost_price, MAX(entry_date) AS latest_entry_date
                    FROM supplier_feed
                    GROUP BY part_id
                )
                SELECT s.part_id, s.stock_level
                FROM latest_entries s
                ORDER BY s.stock_level DESC
                LIMIT 5
            """
        )
        top_stock_levels = cursor.fetchall()

        # find the number of new part_ids added to the supplier_feed each month
        cursor.execute(
            """
                WITH monthly_entries AS (
                    SELECT part_id, strftime('%Y-%m', entry_date) AS entry_month
                    FROM supplier_feed
                )
                SELECT entry_month, COUNT(part_id) AS new_parts_count
                FROM monthly_entries
                GROUP BY entry_month
                ORDER BY entry_month
            """
        )
        new_parts_per_month = cursor.fetchall()

    # plot the average cost_price for each category
    categories, avg_cost_prices_values = zip(*avg_cost_prices)
    fig, ax = plt.subplots()
    cmap = plt.get_cmap('viridis')
    bar_colors = cmap(np.linspace(0, 1, len(categories)))

    bars = ax.bar(categories, avg_cost_prices_values, color=bar_colors)
    ax.set_xlabel('Category', fontweight='bold')
    ax.set_ylabel('Average Cost Price', fontweight='bold')
    ax.set_title('Average Cost Price by Category', fontweight='bold')
    ax.bar_label(bars, label_type='edge', fmt='$%.2f')
    plt.savefig(Path(input_folder) / 'avg_cost_price_by_category.png')

    # plot the number of new part_ids added to the supplier_feed each month
    date, new_parts_count = zip(*new_parts_per_month)
    plt.figure()
    plt.plot(date, new_parts_count)
    plt.xticks(rotation=90)
    plt.xlabel('Date')
    plt.ylabel('Number of New Entries')
    plt.title('New Entries Added Each Month')
    plt.tight_layout()
    plt.savefig(Path(input_folder) / 'new_parts_added_each_month.png')
