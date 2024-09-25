import requests
from bs4 import BeautifulSoup
import csv
import os
import sys
from datetime import datetime

# Ensure UTF-8 output in terminal
sys.stdout.reconfigure(encoding='utf-8')

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

# File to store scraped data
csv_file = 'scraped_data.csv'

# Check if the CSV already exists to avoid overwriting
file_exists = os.path.isfile(csv_file)

# Define the header with the new "מחיר חדש" column
header = ['ID', 'Category', 'Product URL', 'Catalog_id', 'Price', 'מחיר חדש', 'Title', 'Delivery Time', 'Free Shipping', 'Product Image', 'Updated', 'האם המוצר באתר', 'תאריך הוספה', 'תאריך שינוי', 'Type']

# Open the CSV file (in read/write mode if it exists, write mode if it doesn't)
mode = 'r+' if file_exists else 'w'
with open(csv_file, mode=mode, newline='', encoding='utf-8-sig') as file:
    # Create a CSV reader/writer
    reader = csv.reader(file)
    writer = csv.writer(file)
    
    # Write the header row only if the file is new (only once)
    if not file_exists:
        writer.writerow(header)
    
    # Read the existing data into a dictionary (to compare and update if needed)
    previous_data = {row[2]: row for row in reader} if file_exists else {}

    # Initialize an ID counter and a counter for updated products
    id_counter = 1 if not file_exists else len(previous_data) + 1
    updated_count = 0

    # Function to check if row has changed
    def has_data_changed(old_data, new_data):
        return old_data != new_data

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
            if product_url in previous_data:
                old_price = previous_data[product_url][4]
                if old_price != price and price != 'המוצר אינו זמין כרגע':
                    new_price_status = price  # Price has changed
                else:
                    new_price_status = "המחיר לא השתנה"
            else:
                new_price_status = "המחיר לא השתנה"  # No previous price, so assume it's unchanged

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
            if product_url in previous_data:
                product_type = "מוצר קיים"
            else:
                product_type = "מוצר חדש"
            
            # If the product already exists, check for changes
            if product_url in previous_data:
                # Extract the original add date
                date_added = previous_data[product_url][12]
                
                # If data has changed, update 'תאריך שינוי'
                if has_data_changed(previous_data[product_url], [id_counter, category, product_url, catalog_id, price, new_price_status, title, delivery_time, free_shipping, product_image_url, 'Yes', product_status]):
                    date_changed = current_time
                    previous_data[product_url][13] = date_changed  # Update 'תאריך שינוי'
                    updated_count += 1
                else:
                    date_changed = "המוצר לא השתנה מאז הסריקה הקודמת"
                    previous_data[product_url][13] = date_changed  # No changes, keep the old value
            else:
                # For new products, add the current time as 'תאריך הוספה'
                date_added = current_time
                date_changed = "המוצר לא השתנה מאז הסריקה הקודמת"
            
            # Prepare the new row data
            new_data = [
                id_counter, category, product_url, catalog_id, price, new_price_status, title, delivery_time, free_shipping, product_image_url, 'Yes', product_status, date_added, date_changed, product_type
            ]
            
            # Check if the product exists and if its data has changed
            if product_url in previous_data:
                if has_data_changed(previous_data[product_url], new_data):
                    # Update the existing data in the file (overwrite row)
                    previous_data[product_url] = new_data
            else:
                # Add the new product if it doesn't exist
                writer.writerow(new_data)
                previous_data[product_url] = new_data
                print(f"New entry: {product_url}")
            
            # Increment the ID counter
            id_counter += 1

    # Overwrite file with changes, but do not write the header again
    file.seek(0)  # Rewind the file to the beginning
    writer.writerows(previous_data.values())  # Write all rows

# Print summary at the end
if updated_count > 0:
    print(f"Source site scanned, {updated_count} products were updated, and the file was updated successfully")
else:
    print("No changes found in the source site")
