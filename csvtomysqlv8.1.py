import mysql.connector
import csv

# Database connection settings
db_config = {
    'host': 'localhost',
    'user': '',
    'password': '',
    'database': ''
}

# Connect to the WordPress database
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# SQL query to fetch custom meta data for properties (post type) using the correct table prefix wpho_
query = """
SELECT p.ID as post_id, p.post_title, pm.meta_key, pm.meta_value
FROM wpho_posts p
JOIN wpho_postmeta pm ON p.ID = pm.post_id
WHERE p.post_type = 'property'
ORDER BY p.ID, pm.meta_key;
"""

# Execute the query
cursor.execute(query)

# Fetch the results
results = cursor.fetchall()

# Open the CSV file for writing
with open('post_custom_meta.csv', 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)
    # Write the header
    csvwriter.writerow(['post_id', 'post_title', 'meta_key', 'meta_value'])
    
    # Write the rows
    for row in results:
        csvwriter.writerow(row)

# Close the connection
cursor.close()
conn.close()

print("Custom meta data exported to 'post_custom_meta.csv'")
