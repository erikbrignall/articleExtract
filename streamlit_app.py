import requests
import pandas as pd
import json
try:
    from bs4 import BeautifulSoup
except:
    from BeautifulSoup import BeautifulSoup 
from datetime import datetime
import openai
import random # for random header selection
from collections import OrderedDict
from urllib.parse import quote # for url encoding for place lookup
import time
import streamlit as st

openai.api_key = st.secrets["OpenAIapikey"]
GPapikey = st.secrets["GPapikey"]

###### FUNCTION EXTRACT VALUES FROM JSON
## The below function loops through the JSON structure and returns any value matching the key
def extract_values(obj, key):
        """Pull all values of specified key from nested JSON."""
        arr = []

        def extract(obj, arr, key):
            """Recursively search for values of key in JSON tree."""
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, (dict, list)):
                        extract(v, arr, key)
                    elif k == key:
                        arr.append(v)
            elif isinstance(obj, list):
                for item in obj:
                    extract(item, arr, key)
            return arr

        results = extract(obj, arr, key)
        return results

###### FUNCTION TO EXTRACT ELEMENTS FROM JSON RESPONSE AND FIND LATLONG
def extractjson(obj):
    # Date
    try:
        date1 = json_obj['date']
    except:
        date1 = datetime.now()
    # title
    try:
        title = json_obj['title']
    except:
        title = datetime.now() 
    try:
        vehicles = json_obj['vehicles']
    except:
        vehicles = "0"
    try:
        place = json_obj['place']
    except:
        place = "Not found"
    # county
    try:
        county = json_obj['county']
    except:
        county = "Not found"
    # typeofland
    try:
        typeofland = json_obj['typeofland']
    except:
        typeofland = "Not found"
    # source
    try:
        source = json_obj['source']
    except:
        source = "Not found"
    
    # Extract latlong from google places API
    placeurl = quote(place)
    url = "https://maps.googleapis.com/maps/api/geocode/json?address=" + placeurl +"&key=" + GPapikey
    print(url)
    try:    
        responseloc = requests.get(url)
        data = json.dumps(responseloc.json(), sort_keys=True, indent=4)
        data = json.loads(data)
    except:
        data = "no response"

    if data != "no response":
        try:
            lat = extract_values(data,"lat")
            lat = str(lat[0])
            lat = lat[:7]
                    
        except:
            lat = "not found"

        try:
            long = extract_values(data,"lng")
            long = str(long[0])
            long = long[:7]
        except:
            long = "not found"

        latlong = lat + ", " + long
    else:
        latlong = "0,0"
    
    
    row = [date1,title,vehicles,place,typeofland,county,latlong,source]
    return(row)

##########


# setup rotating headers 
headers_list = [        
    {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0}",    
    "Accept-Encoding": "gzip, deflate", 
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"    
    },
    {    
    "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 Safari/605.1.15",   
    "Accept-Encoding": "gzip, deflate", 
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    }   
    ]

# Create ordered list of headers for random selection
ordered_headers_list = []
for headers in headers_list:
    h = OrderedDict()
    for header,value in headers.items():
        h[header]=value
        ordered_headers_list.append(h)
        
###############

st.set_page_config(page_title='News Data Extractor - DEMO')
st.image('logo-temp2.PNG', width=200)
st.write('The following is a demo of the use of LLMs to extract and structure data from news articles to facilitate analysis including fetching the data from the provided links')

# Page title
st.title('News Data Extractor - DEMO')

# upload list of weblinks for analysis
filename = st.file_uploader('Upload a CSV file', type=['csv'])

if filename is not None:
    df = pd.read_csv(filename)
    articles  = df['articles']

    # create dataframe to store outputs
    dfACols = {'date': [],'title': [],'vehicles': [], 'place': [], 'type_land ':[], 'county': [], 'latlong': [], 'source': []}
    dfA = pd.DataFrame(data = dfACols)
    
    for url in articles:
    
        # Select a random header
        headers = random.choice(headers_list)
        response = requests.get(url, headers=headers)
    
        # Check if the GET request is successful
        if response.status_code == 200:
            # Create a BeautifulSoup object and specify the parser
            soup = BeautifulSoup(response.text, 'html.parser')
    
            # Find the main content of the article. You need to inspect the HTML of the webpage to find the appropriate tag and class name.
            # In this example, we assume that the main content is in a <div> tag with class name 'article-content'.
            headers = soup.find_all(['h1', 'h2', 'p'])
    
            article = ""
    
            if headers:
                # Extract and print the textual content of each tag
                for tag in headers:
                    #print(tag.name.upper())
                    #print(tag.get_text(strip=True))
                    x = tag.get_text(strip=True)
                    article = article + ". " + x + " "
                    article = article.split()
                    article = article[:250]
                    article = ' '.join(article)
    
            else:
                print("Could not find any header or paragraph content.")
        else:
            print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
    
        article = article + " " + url
        
        messages=[
            {"role": "system", "content": "You are a news analyst who extracts and summarises news articles about traveller and gypsy encampments. You extract 7 different pieces\
            of content from a provided news article and returning them as a json object of key value pairs exactly as specified here ( \
            date: the date of the incident, if not present use the date 14/09/2023, \
            title: a suggested article title of around 6 words, \
            vehicles: the number of caravans or vehicles if mentioned displayed solely as an integer, \
            place: the address where the encampment has occured including street, town and county if given,\
            county: the UK county for the location, e.g. berkshire/hampshire/yorkshire if you can infer that from the location, \
            typeofland: specify public/private if found, \
            source: the first URL given in the text if any)."},
            {"role": "user", "content": article}
        ]
    
        # FETCH RESPONSE
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            temperature = 0.1,
            stop = None,
            messages=messages)
    
        response_text = response.choices[0].message.content
        response_text = response_text.replace('\n', ' ').lower()
        json_obj = json.loads(response_text)
        
        row = extractjson(response_text)
        #print(row)
        
        dfA.loc[len(dfA.index)] = row
        time.sleep(3)
        
        
    st.dataframe(dfA, width=800)
    def convert_df_to_csv(df):
      return df.to_csv().encode('utf-8')
    
    st.download_button(
      label="Download data as CSV",
      data=convert_df_to_csv(dfA),
      file_name='article_summarys.csv',
      mime='text/csv',
    )
