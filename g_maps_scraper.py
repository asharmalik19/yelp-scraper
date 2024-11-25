from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import re
from selenium.webdriver.common.keys import Keys
import pandas as pd
from datetime import datetime
import time
from selenium.common.exceptions import NoSuchElementException
import logging
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def search(driver, search_query):
    URL = 'https://www.google.com/maps'
    driver.get(URL)
    search_box_id = 'searchboxinput'
    search_box = driver.find_element(By.ID, search_box_id)
    search_box.send_keys(search_query)
    search_box.send_keys(Keys.RETURN)
    return

def get_links(driver):
    results_selector = '//a[@class="hfpxzc"]'
    results = driver.find_elements(By.XPATH, results_selector)
    result_links =  [result.get_attribute('href') for result in results]
    return result_links

def scrape_business_details(driver, link):  
    driver.get(link)
    title_selector = 'h1.DUwDvf.lfPIob'
    business_title = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, title_selector))).text
    business_title = business_title.replace('"', '')
    business_title = business_title.replace("'", '')
    print(f'buinsess title: {business_title}')

    type_selector = 'button.DkEaL '  # using findelements instead of findelement to avoid exception handling
    business_type = driver.find_elements(By.CSS_SELECTOR, type_selector)
    if business_type:
        business_type = business_type[0].text.strip()
        print(f'business type: {business_type}')
    else:
        business_type = ''
        print('business type not found')

    address_selector = 'button[data-item-id="address"] div.rogA2c'
    address = driver.find_elements(By.CSS_SELECTOR, address_selector)  
    if address:
        address = address[0].text.strip()
        print(f'address: {address}')
    else:
        address = ''
        print('address not found')

    # selecting the website link
    website_link_selector = 'a[data-tooltip="Open website"]'
    website_link = driver.find_elements(By.CSS_SELECTOR, website_link_selector)
    if website_link:
        website_link = website_link[0].get_attribute('href')  # the return data type was a set, thus needed to be type casted
        print(f'website link: {website_link}')
    else:
        website_link = ''
        print('website link not found')

    domain_pattern = re.compile(r'\b(?:https?://)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b') # todo: proper testing required
    # number_pattern = re.compile(r'\+\d{1,2} \d{3}-\d{3}-\d{4}')
    number_pattern = re.compile(r'\+\d{1,2} \d{3}[-\s]?\d{3}[-\s]?\d{3,4}')

    # Check if a business is temporarily closed or permanantly
    closed_business_selector = 'span.fCEvvc'
    closed_business = driver.find_elements(By.CSS_SELECTOR, closed_business_selector)
    if closed_business:
        business_status = closed_business[0].text.strip()
        print(f'closed business: {business_status}')
    else:
        business_status = ''
        print('closed business not found')

    # I'm making dynamic selector which changes with the business title to get the div of contact details
    contact_details_div_selector = f'div[aria-label="Information for {business_title}"]'  # todo: this selector doesn't work for toledo city
    contact_details_div = driver.find_elements(By.CSS_SELECTOR, contact_details_div_selector)
    if not contact_details_div:
        return [business_title, '', address, '', '', business_type, business_status]  # return where the business don't have contact details
    
    contact_details_text = contact_details_div[0].get_property('innerText')
    match = domain_pattern.search(contact_details_text)
    if match:
        domain_name = match.group()
        print(f'domain_name: {domain_name}')
    else:
        domain_name = ''
        print('domain_name not found')
    
    num_match = number_pattern.search(contact_details_text)
    if num_match:
        number = num_match.group()
        print(f'number: {number}')
    else:
        number = ''
        print('number not found')

    business_details = [business_title, number, address, domain_name, website_link, business_type, business_status]    
    return business_details


def get_driver(headless=False):
    # path = r'C:\Users\Wellnessliving\Downloads\chromedriver.exe'
    if headless:
        options_headless = webdriver.ChromeOptions()  
        options_headless.add_argument('--headless')
        options_headless.add_argument('--blink-settings=imagesEnabled=false')
        options_headless.add_experimental_option("detach", True)
        options_headless.add_argument('--disable-dev-shm-usage')
        options_headless.add_argument("--window-position=-2400,-2400")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options_headless)

        # service = ChromeService(executable_path=path)
        # driver = webdriver.Chrome(service=service, options=options_headless)
        print('headless driver created!')
    else:
        options = webdriver.ChromeOptions()
        options.add_experimental_option("detach", True)
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        # service = ChromeService(executable_path=path)
        # driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(5)
        print('headfull driver created!')
    return driver

def make_search_query(keyword, location):
    keyword = keyword + ' in '
    location = ', '.join(i for i in location.values())
    search_query = keyword + location
    return search_query

def remove_duplicates(data_df):
    columns_to_check = ['Company', 'Number', 'Address']
    data_df_without_duplicates = data_df[~data_df.duplicated(subset=columns_to_check, keep='first')]
    return data_df_without_duplicates
    
def scroll(driver, search_query):
    try:
        div_sidebar=driver.find_element(By.CSS_SELECTOR,f"div[aria-label='Results for {search_query}']")
    except NoSuchElementException:
        return

    keepScrolling=True
    while(keepScrolling):
        div_sidebar.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.5)
        div_sidebar.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.5)
        html = driver.find_element(By.TAG_NAME, "html").get_attribute('outerHTML')
        if(html.find("You've reached the end of the list.")!=-1):
            keepScrolling=False
    return 


if __name__=='__main__':
    start_time = datetime.now()

    df = pd.read_csv('keywords.csv')
    keyword_list = df.loc[df['status'].str.lower() == 'on', 'keywords'].to_list()

    # read the cities
    cities_df = pd.read_csv('cities.csv')
    cities = cities_df['City'].to_list()

    logging.basicConfig(filename=f'g_map_scraper.log', filemode='w', level=logging.ERROR)
    logging.info(f'cities: {cities}')

    for city in cities:
        LOCATION = {
            'city': f'{city}',
            'state': 'PA',
            'country': 'USA'
        }

        df_columns = [
                'Company',
                'Number',
                'Address',
                'Domain',
                'Website',
                'Business Type',
                'Business Status',
                'State',
                'Keyword'
            ]
        data_df = pd.DataFrame(columns=df_columns)
        driver = get_driver()
        driver_headless = get_driver(headless=True)

        # try:
        for keyword in keyword_list:
            search_query = make_search_query(keyword=keyword, location=LOCATION)
            search(driver=driver, search_query=search_query)
            time.sleep(4)
        
            scroll(driver=driver, search_query=search_query)
            result_links = get_links(driver=driver)
            if not result_links:  # empty list of result links means that its a business page
                print(f'No results found for {keyword}')
                continue

            for link in result_links: 
                try:  # if a business page takes too long to load, it throws exception when scraping the title
                    business_details = scrape_business_details(driver=driver_headless, link=link)
                except TimeoutException as e:
                    logging.error(f'skipping {link} in city {LOCATION["city"]} for keyword {keyword}: {e}')
                    continue

                business_details.append(LOCATION['state'])  # appending info other than the scraped data
                business_details.append(keyword)       
                data_df.loc[len(data_df)] = business_details
                print('-------------------------------------------------------')
        # except Exception as e:
        #     logging.error(f'the keyword loop did not complete for city {LOCATION["city"]}: keyword: {keyword}: {e}')

        data_df_without_duplicates = remove_duplicates(data_df=data_df)
        file_name = f'{LOCATION["city"]}.xlsx'
        data_df_without_duplicates.to_excel(file_name, index=False)  
        
        driver.quit()
        driver_headless.quit()

        print(f'the {LOCATION["city"]} has been scraped!')
        logging.info(f'the {LOCATION["city"]} has been scraped properly!')
        end_time = datetime.now()
        print(end_time - start_time)

        


# extra notes:
# the log file is created for a run. If the script is crashed and re-run, new log file will be created
    





