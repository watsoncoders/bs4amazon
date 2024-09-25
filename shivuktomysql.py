import requests
from bs4 import BeautifulSoup
import mysql.connector
from datetime import datetime
from urllib.parse import urlparse

# Ensure UTF-8 output in terminal
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Connect to MySQL
db_connection = mysql.connector.connect(
    host='localhost',
    user='your_mysql_user',
    password='your_mysql_password',
    database='your_database_name'
)

cursor = db_connection.cursor()

# Read URLs from a file called 'categories.txt'
def load_urls_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]  # Strip any empty lines
    return urls

# Check the status of the URL (200 for OK, 404 for Not Found)
def check_product_status(url):
    try:
        response = requests.head(url, allow_redirects=True)
        if response.status_code == 200:
            return "המוצר זמין באתר"
        else:
            return "המוצר לא זמין כעת"
    except:
        return "המוצר לא זמין כעת"

# Load URLs from 'categories.txt'
url_file = 'categories.txt'
urls = load_urls_from_file(url_file)

# Function to insert data into MySQL
def insert_data_into_mysql(data):
    query = """
    INSERT INTO product_data (category, product_url, catalog_id, price, new_price, title, delivery_time, free_shipping, product_image, updated, product_status, date_added, date_changed, product_type, datasource)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        price = VALUES(price),
        new_price = VALUES(new_price),
        title = VALUES(title),
        delivery_time = VALUES(delivery_time),
        free_shipping = VALUES(free_shipping),
        product_image = VALUES(product_image),
        updated = VALUES(updated),
        product_status = VALUES(product_status),
        date_changed = VALUES(date_changed),
        product_type = VALUES(product_type),
        datasource = VALUES(datasource)
    """
    cursor.execute(query, data)
    db_connection.commit()

# Get current date and time
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Loop through each URL
for url in urls:
    print("URL scraped successfully")  # English message
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'lxml')
    
    # Extract the category name from <li class="cell active"> element
    category_li = soup.find('li', class_='cell active')
    category = category_li.find('a')['title'] if category_li and category_li.find('a') else 'N/A'
    
    # Extract the host (datasource)
    parsed_url = urlparse(url)
    datasource = parsed_url.hostname
    
    # Find all <li> elements with class 'cell productItem'
    product_items = soup.find_all('li', class_='cell productItem')
    
    # Loop through each product item
    for item in product_items:
        # Extract the product URL from the <a> tag inside <li class="cell productItem">
        product_url = item.find('a')['href'] if item.find('a') else 'N/A'
        
        # Extract the Catalog_id from the <li class="cell productItem" data-id="...">
        catalog_id = item['data-id'] if 'data-id' in item.attrs else 'N/A'
        
        # Price (if available) and handle empty price scenario
        price = item.find('span', itemprop='price').get_text(strip=True) if item.find('span', itemprop='price') else 'המוצר אינו זמין כרגע'
        
        # Check if the price has changed
        new_price_status = "המחיר לא השתנה"
        
        # Title from <div class="title titleIndex" itemprop="name"><h2>
        title_div = item.find('div', class_='title titleIndex')
        title = title_div.find('h2').get_text(strip=True) if title_div and title_div.find('h2') else 'N/A'
        
        # Free Shipping (משלוח חינם) if <div class="imtext hanaha"> exists, else 'no free shipping'
        free_shipping = 'Free shipping' if item.find('div', class_='imtext hanaha') else 'No free shipping'
        
        # Delivery Time (from class 'stiker'), if empty return 'Not specified'
        delivery_time = item.find('div', class_='stiker').get_text(strip=True) if item.find('div', class_='stiker') else 'Not specified'
        
        # Product Image URL (from <div class="catalog_image"><img src=...>)
        catalog_image = item.find('div', class_='catalog_image')
        product_image_url = catalog_image.find('img')['src'] if catalog_image and catalog_image.find('img') else 'N/A'
        
        # Check if the product is still available (status code)
        product_status = check_product_status(product_url)
        
        # Determine the type of product (new or existing)
        product_type = "מוצר חדש"

        # For new products, add the current time as 'תאריך הוספה'
        date_added = current_time
        date_changed = "המוצר לא השתנה מאז הסריקה הקודמת"
        
        # Prepare the new data
        data = (
            category, product_url, catalog_id, price, new_price_status, title, delivery_time, free_shipping, product_image_url, 'Yes', product_status, date_added, date_changed, product_type, datasource
        )
        
        # Insert the data into MySQL
        insert_data_into_mysql(data)

# Close MySQL connection
cursor.close()
db_connection.close()
