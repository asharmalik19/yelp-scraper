import scrapy
from scrapy.linkextractors import LinkExtractor
import pandas as pd
from urllib.parse import urljoin, urlparse
import re


class BookingSpider(scrapy.Spider):
    name = "class_bookings"   
    df = pd.read_excel("input/Classes_checks_cleaned.xlsx")

    keywords = ["class", "appointment"]

    def start_requests(self):
        for _, row in self.df.iterrows():
            domain_url = row["Domain"]
            account_id = row["Account ID"]
            yield scrapy.Request(
                url=domain_url, 
                callback=self.parse_homepage,
                meta={"account_id": account_id}
            )


    def parse_homepage(self, response):
        if self.find_the_relevant_link(response):
            return
        internal_links = self.get_all_internal_links(response)
        for link in internal_links:
            yield response.follow(
                link, 
                callback=self.find_the_relevant_link, 
                meta={"account_id": response.meta['account_id']}
            )


    def find_the_relevant_link(self, response):
        links = LinkExtractor().extract_links(response)
        for link in links:
            if self.is_relevant_link(link.url, link.text):
                yield {
                    "account_id": response.meta['account_id'],
                    "found_on": response.url,
                    "relevant_link": link.url
                }
                return True
        return False

    
    def is_relevant_link(self, url, text=None):

        url = url.lower()
        text = text.lower() if text else ""

        for keyword in self.keywords:
            if keyword in url or keyword in text:
                return True

        return False
    
    
    def get_all_internal_links(self, response):
  
        base_url = response.url
        internal_links = set()

        links_on_homepage = LinkExtractor(allow_domains=[base_url])

        for link in links_on_homepage:
            if link.url.startswith(('tel:', 'mailto:', 'javascript:')) or re.search(r'\.(png|jpg|jpeg|pdf|docx|css|js)$', link.url):
                continue
            internal_links.add(link.url)

        return list(internal_links)[:50]
    
