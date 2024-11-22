from bs4 import BeautifulSoup
from curl_cffi import requests
import pandas as pd
from dotenv import load_dotenv
import os


# url = 'https://www.yelp.com/search?find_desc=yoga+studio+&find_loc=jefferson%2C+kentucky&start=0'
# r = requests.get(url, impersonate='chrome101')
# print(r.status_code)
# print(r.content)

# requests.get('https://api.scrapingdog.com/scrape?dynamic=false&api_key=Your-API-key&url=


def scrape_business_page(content):
    soup = BeautifulSoup(content, 'html.parser')
    
    # Define a helper function to safely get text
    def get_text(element):
        return element.get_text(strip=True) if element else None
    
    title_selector = 'h1.y-css-olzveb'
    business_type_selector = 'span.y-css-1w2z0ld'
    website_selector = 'p.y-css-1o34y7f a.y-css-1rq499d'
    address_selector = 'div.y-css-cxcdjj p.y-css-dg8xxd'
    phone_selector = 'div.y-css-cxcdjj p.y-css-1o34y7f'
    
    # Use dictionary comprehension to build the result dictionary
    business_info = {
        'title': get_text(soup.select_one(title_selector)),
        'business_type': get_text(soup.select_one(business_type_selector)),
        'website': get_text(soup.select_one(website_selector)),
        'address': get_text(soup.select_one(address_selector)),
        'phone': get_text(soup.select(phone_selector)[1] if len(soup.select(phone_selector)) == 3 else None)
    }  
    return business_info

def fetch_business_links(content):
    BASE_URL = 'https://www.yelp.com'
    soup = BeautifulSoup(content, 'html.parser')
    business_links = soup.select('div.businessName__09f24__HG_pC.y-css-ohs7lg a')
    business_links = [BASE_URL + link['href'] for link in business_links]
    return business_links

def make_request(url, API_KEY):
    # r = requests.get(url, impersonate='chrome101')
    r = requests.get(f'https://api.scrapingdog.com/scrape?dynamic=false&api_key={API_KEY}&url={url}')
    if r.status_code != 200:
        print(r.status_code)
        print(r.content)
        # print('invalid status code encountered! ending the script')
        return None
    return r.content

def main():

    load_dotenv()
    API_KEY = os.getenv('SCRAPING_DOG_API_KEY')

    businesses_no = 0
    while True:
        url = f'https://www.yelp.com/search?find_desc=yoga+studio+&find_loc=jefferson%2C+kentucky&start={businesses_no}'
        
        content = make_request(url, API_KEY)
        if content is None:
            break

        business_links = fetch_business_links(content)
        print(business_links)

        businesses = []
        for link in business_links:
            content = make_request(link, API_KEY)
            if content is None:
                break
            business_info = scrape_business_page(content)
            print(business_info)
            businesses.append(business_info)
        
        df = pd.DataFrame(businesses)
        df.to_csv('yelp.csv', mode='a', index=False)

        businesses_no += 10

        # temp
        break
    return


if __name__=='__main__':
    # url = 'https://www.yelp.com/biz/bend-and-zen-hot-yoga-louisville-2?osq=yoga+studio'
    main()
    
    

    

    # r = requests.get(url, impersonate='chrome101')

    # business_info = scrape_business_page(r.content)

    # print(business_info)
