import requests
from dotenv import load_dotenv
import os
import pandas as pd

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv('YELP_FUSION_KEY')

# Yelp API base URL
BASE_URL = "https://api.yelp.com/v3/businesses/search"

# HTTP headers for authentication
HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'accept': 'application/json'
}

# Output CSV file
OUTPUT_FILE = "yoga_businesses_in_california.csv"


def get_business_list(term, location):
    """
    Query the Yelp API to fetch yoga businesses in a specific city.
    """
    params = {
        'term': term,
        'location': location,
        'attributes': 'hot_and_new',
    }
    response = requests.get(BASE_URL, headers=HEADERS, params=params)
    return response.json().get('businesses')


def parse_business_data(business):
    """
    Parse relevant fields from the business JSON object.
    """
    name = business.get('name', 'N/A')
    phone = business.get('phone', 'N/A')
    
    # get address from the location key
    location = business.get('location')
    address1 = location.get('address1', 'N/A')  
    zip_code = location.get('zip_code', 'N/A')
    city = location.get('city', 'N/A')
    state = location.get('state', 'N/A')
    country = location.get('country', 'N/A')

    category = business.get('categories')[0].get('title', 'N/A')  # will give error if no categories key

    # get some info from the attributes key
    attributes = business.get('attributes')
    business_url = attributes.get('business_url', 'N/A')
    hot_and_new = attributes.get('hot_and_new', 'N/A')

    return {
        'Name': name,
        'Website': business_url,
        'Phone': phone,
        'street': address1,
        'Zip Code': zip_code,
        'City': city,
        'State': state,
        'Country': country,
        'Category': category,
        'Hot and New': hot_and_new
    }


def main():
    term = 'fitness studio'
    all_businesses = []
    cities = pd.read_csv('cities.csv')['City'].tolist()

    print(cities)

    for city in cities:
        location = city + ', CA'
        print(f"Fetching {term} businesses for {location}...")
        business_list = get_business_list(term, location)

        for business in business_list:
            parsed_data = parse_business_data(business)
            print(parsed_data)
            print('-------------------------------')
            all_businesses.append(parsed_data)

    output_df = pd.DataFrame(all_businesses)
    output_df.to_csv(f'{term}.csv', index=False)




if __name__ == '__main__':
    main()
