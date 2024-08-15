import requests
from bs4 import BeautifulSoup
import pandas as pd
import pickle
import os
from lxml import etree

class Scraper:
    def __init__(self, urls_file):
        self.urls_file = urls_file
        self.progress_file = 'progress.pkl'
        self.csv_file = 'scraped_data.csv'
        self.urls = self.load_urls()

        # Initialize CSV file with headers if it doesn't exist
        if not os.path.exists(self.csv_file):
            df = pd.DataFrame(columns=[
                'URL', 'Title_HTML', 'Price_HTML', 'Image_HTML', 'Twister_HTML', 'Color_HTML', 
                'Color_List_HTML', 'Features_HTML', 'CorePrice_HTML', 'Delivery_HTML', 
                'Delivery_Message_HTML', 'Merchant_Info_HTML'
            ])
            df.to_csv(self.csv_file, index=False, encoding='utf-8-sig')

    def load_urls(self):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'rb') as f:
                return pickle.load(f)
        else:
            with open(self.urls_file, 'r', encoding='utf-8') as f:
                return f.read().splitlines()

    def save_progress(self):
        with open(self.progress_file, 'wb') as f:
            pickle.dump(self.urls, f)

    def scrape(self):
        for url in self.urls[:]:  # Iterate over a copy of the list
            print(f"Scraping {url}...")
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'lxml')

            # Convert the soup to an lxml object
            dom = etree.HTML(str(soup))

            data = {
                'URL': url,
                'Title_HTML': self.extract_xpath_html(dom, '//*[@id="title_feature_div"]'),
                'Price_HTML': self.extract_xpath_html(dom, '//*[@id="corePriceDisplay_desktop_feature_div"]/div[1]/span[2]'),
                'Image_HTML': self.extract_xpath_html(dom, '//*[@id="main-image-container"]/ul/li[1]/span'),
                'Twister_HTML': self.extract_xpath_html(dom, '//*[@id="twister_feature_div"]'),
                'Color_HTML': self.extract_xpath_html(dom, '//*[@id="variation_color_name"]/div'),
                'Color_List_HTML': self.extract_xpath_html(dom, '//*[@id="variation_color_name"]/ul'),
                'Features_HTML': self.extract_xpath_html(dom, '//*[@id="feature-bullets"]'),
                'CorePrice_HTML': self.extract_xpath_html(dom, '//*[@id="corePrice_feature_div"]/div/div'),
                'Delivery_HTML': self.extract_xpath_html(dom, '//*[@id="deliveryBlockSelectAsin"]'),
                'Delivery_Message_HTML': self.extract_xpath_html(dom, '//*[@id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE"]/span'),
                'Merchant_Info_HTML': self.extract_xpath_html(dom, '//*[@id="merchantInfoFeature_feature_div"]/div[2]/div/span')
            }

            # Save the data into the CSV file
            df = pd.DataFrame([data])
            df.to_csv(self.csv_file, mode='a', header=False, index=False, encoding='utf-8-sig')

            # Remove the scraped URL from the list and save progress
            self.urls.remove(url)
            self.save_progress()

            print(f"Scraped {len(self.urls)} remaining links.")

        # If finished, remove the progress file
        if not self.urls:
            os.remove(self.progress_file)

    def extract_xpath_html(self, dom, xpath):
        elements = dom.xpath(xpath)
        if elements:
            # If it's a valid HTML element, return the HTML content
            return etree.tostring(elements[0], encoding='unicode', pretty_print=True) if elements else 'לא צויין על ידי המפרסם'
        return 'לא צויין על ידי המפרסם'

if __name__ == "__main__":
    # The file containing the list of URLs
    urls_file = 'amazon.txt'

    # Create scraper instance and start scraping
    scraper = Scraper(urls_file)
    scraper.scrape()
