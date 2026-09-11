
# Project: Supplier Data Integration & Analysis Pipeline

## Objective
Parts Avatar is looking to integrate a new auto parts supplier to expand our inventory. We have received a sample data feed (`supplier_feed.csv`) containing their product stock levels and costs, along with a separate file (`product_metadata.csv`) that maps supplier part IDs to our internal product information.

Our goal is to build a reliable, automated pipeline to process this data, load it into a database, and perform an initial analysis to determine the viability of this supplier.

## The Challenge
The supplier's data feed is notoriously unreliable. It contains inconsistencies, missing values, and mixed data types that must be handled gracefully. Your task is to design and implement a small-scale ETL (Extract, Transform, Load) pipeline that is robust enough to handle these issues and produce clean, analytics-ready data.

## Datasets
* `data/supplier_feed.csv`: The raw, messy data from the new supplier.
* `data/product_metadata.csv`: Maps the supplier's parts to our internal system.

## Your Tasks
1.  **Extract & Transform:**
    * Write a Python script (`src/transform_data.py`) to read, clean, and standardize the `supplier_feed.csv` data.
    * **Problem-Solving:** You must make and document key decisions. For example: How do you handle "Low Stock"? How do you impute missing `cost_price` values? What is your strategy for standardizing the messy `entry_date` column? Justify your choices in this README.

2.  **Load:**
    * Create a simple SQLite database (`parts_avatar.db`).
    * Load the cleaned supplier data and the product metadata into two separate tables in the database. Ensure the data types are correct and consider setting up primary keys.

3.  **Analyze & Visualize:**
    * Write a Python script or a Jupyter Notebook to query the SQLite database and answer the following business questions:
        * What is the average cost price per product category?
        * Which top 5 parts have the highest stock levels right now?
        * How has the number of new parts entries from this supplier changed over time (on a monthly basis)?
    * Create at least two clear and informative visualizations (e.g., using Matplotlib, Seaborn, or Plotly) to present your findings.

4.  **Documentation:**
    * Update this `README.md` file to be a comprehensive report of your project.
    * Explain your data cleaning strategies and justify your decisions.
    * Describe the schema of your database tables.
    * Present your findings from the analysis, including the visualizations you created.
    * Provide clear instructions on how to run your entire pipeline from start to finish.

## Evaluation Criteria
* **Problem-Solving:** The logic and justification behind your data cleaning and transformation decisions.
* **Python & SQL Proficiency:** The quality, efficiency, and organization of your code.
* **Data Engineering Concepts:** The structure and robustness of your ETL pipeline.
* **Data Visualization & Communication:** The clarity and impact of your analysis and visualizations in the README report.

## Disclaimer: Data and Evaluation Criteria
Please be advised that the datasets utilized in this project are synthetically generated and intended for illustrative purposes only. Furthermore, they have been significantly reduced in terms of sample size and the number of features to streamline the exercise. They do not represent or correspond to any actual business data. The primary objective of this evaluation is to assess the problem-solving methodology and the strategic approach employed, not necessarily the best possible tailored solution for the data. 

## Project Report
1. **Extract and Transform**
    * The first step of any project like this one is to explore the data. The main things to look for are: what are the different values and datatypes that appear in each of the columns, how can they be consolidated to a single format and what columns could be potentially used as primary keys, if there are any, ensure that values are unique.
    * The file I used for this exploration is explore_data.ipynb.
    * In the notebook, I performed the following operations: identify the datatypes and formats present in the columns of both .csv files, elaborate and test methods to consolidate all the data to a consistent format and determine how to construct the database based on the information required to conduct the analysis and construct the visualisations for part 3.

#### Findings from explore_data.ipynb
    Given the fact that one of the metrics that needs to be tracked is the number of updates to quantities per month, all entries must be kept, simply handling the invalid elements of entries as they come up.

    For the error handling, only two columns can contain errors: stock_level and cost_price. The stock_level column can contain the labels "UNAVAILABLE" and "LOW STOCK", among others. For our purposes, I think that assuming that any non-numerical entries should be treated as zero. The reason for this being that "UNAVAILABLE" clearly indicates zero, and "LOW STOCK" could indicate anything from 100s to dozens to actually depleted stock, depending on the supplier's arbitrary internal conventions that are unknown to us. Thus, we default to zero. For cost_price, a missing value can simply indicate that the stock of an item has changed, but not the price. Consequently, when a price is missing, we can fill the cost_price field with the most recent valid value for the same item, and if no such value exists, then we leave the NaN value to inform us that we need to contact the supplier to obtain pricing information if we have no other entries in our database with that part_id that have a valid price.

    In summary, the cleaning and formatting pipeline will function as such:
        - transform the cost_price and entry_date columns to the correct formats and datatypes
        - default all invalid stock_level entries to 0
        - sort by part_id
    
2. **Load**
    * The method I used to set up the database was to first run my cleaning script on the .csv files, then use the sqlite3 package to create a connection and delete any exsisting tables in the database file with names matching `supplier_feed` and `product_metadata` to ensure that there are no issues when I create the tables and insert the data.
    * I decided to make `part_id` the primary key in the `product_metadata` table, as I found it to be unique in my exploration and, given the fact that that the table is meant to represent a one-to-one relationship, it is a necessary constraint to enforce. On the other hand, I did not choose any primary key for the `supplier_feed` table, as it represents a many-to-many relationship between part_ids and updates to stock and price.

3.  **Analyze & Visualize:**
    * Here I will outline how I interpreted each analysis task:
        * **What is the average cost price per product category?**: For this task, I decided to use only the prices from the most recent entries for each part_id. I made this decision because, in a real business context, averaging over all entries would taint the results. Changes in market conditions and inflation affect prices throughout time and parts with a larger number of entries could drown out parts with few entries when taking averages. Consequently, my decision was necessary to ensure that the averages over part categories are accurate when considering current prices.
        * **Which top 5 parts have the highest stock levels right now?**: Following the same logic I used for the previous task, I considered only the most recent entries for each part_id. In the case of this task, the statement "right now" indicates that we are looking for the most up-to-date information regarding product inventory.
        * **How has the number of new parts entries from this supplier changed over time (on a monthly basis)?**: Here, I considered a "new parts entry" to be any entry in the `supplier_feed` table, as considering only the first time each part_id appears yields a very ininteresting result (each part_id appears at least once in the first 2 months of the dataset). Consequently, to produce the results, I simply converted the `entry_date` column from yyyy-mm-dd format to yyyy-mm format, grouped by date to count the number of entries then sorted in ascending order.

    * For the visualization element, I decided to use the results from the *average cost per category* and *new parts entries over time* tasks. I chose *average cost per category* as my first visualization because, upon seeing the results of the analysis, I noticed that all of the average price values were rather similar, but not identical. Consequently, a bar plot is a great tool to understand the price distribution, as the differences in heights facilitates a quick understanding of the data in a way that is not possible by simply looking at the numbers and calculating percentage differences. As for *new parts entries over time*, this was the first analysis I thought of visualizing upon reading this project's instructions because it is utterly impossible to properly identify long term trends in data just by looking at numbers.

### Database Schema
```
Table supplier_feed {
    part_id text [not null]
    stock_level integer
    cost_price real
    entry_date text
}
```

```
Table product_metadata {
    part_id text [primary key]
    part_name text
    category text
}
```

### How to run the pipeline
The pipeline is entirely contained in the transform_data.py file.
```
pip install -r requirements.txt
```
```
python ./src/transform_data.py
```