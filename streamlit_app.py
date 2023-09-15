import openai
import pandas as pd
import re #regex for extracting data from response
from urllib.parse import quote # for url encoding for place lookup
import requests
import time
import json
import streamlit as st

st.set_page_config(page_title='News Data Extractor - DEMO')
st.image('logo-temp2.PNG', width=200)
st.write('The following is a demo of the use of LLMs to extract and structure data from news articles to facilitate analysis')

openai.api_key = st.secrets["OpenAIapikey"]
GPapikey = st.secrets["GPapikey"]

# Page title

st.title('News Data Extractor - DEMO')

# UPLOAD ARTICLES
st.write('Paste the article to be analysed in the field below. Ideally paste: Title, URL, Article content as text')

# Create a large text input field
with st.form(key='my_form_to_submit'):
    st.write('Please input your query to generate the appropriate chart:')
    user_input = st.text_area("Enter Text Here", height=300)
    submit_button = st.form_submit_button(label='Submit')

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

dfACols = {'date': [],'title': [],'vehicles': [], 'place': [], 'type_land ':[], 'county': [], 'latlong': [], 'source': []}
dfA = pd.DataFrame(data = dfACols)

if submit_button and user_input is not None:

        article = user_input.replace('\n', ' ')

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

        st.write(response_text)
            
        # extract individual elements from response

        ## DATE
        #try:
        #    pattern = r'date: (.*?)title:'
        #    match = re.findall(pattern, response_text)
        #    art_date = match[0]
        #except:
        #    art_date = response_text["date"]
    
        ## TITLE
        try:
            pattern = r'title: (.*?)vehicles:'
            match = re.findall(pattern, response_text)
            art_title = match[0]
        except:
            art_title = response_text["title"]

        ## VEHICLES
        try:    
            pattern = r'vehicles: (.*?)place:'
            match = re.findall(pattern, response_text)
            art_vehicles = match[0]
        except:
            art_vehicles = response_text["vehicles"]
            
        ## COUNTY
        try:
            pattern = r'county: (.*?)type of land:'
            match = re.findall(pattern, response_text)
            art_county = response.text["county"]
        except:
            art_county = "unknown"

        ## PLACE
        try:
            pattern = r'place: (.*)county:'
            match = re.findall(pattern, response_text)
            places = match[0]
            placeurl = quote(places)
        except:
            places = response.text["place"]
            placeurl = quote(places)
        
        ## TYPELAND
        try:
            pattern = r'type of land: (.*?)source:'
            match = re.findall(pattern, response_text)
            type_land = match[0]
        except:
            type_land = response_text["typeofland"]
        
        ##SOURCE
        try:    
            pattern = r'source: (.*)'
            match = re.findall(pattern, response_text)
            art_source = match[0]
        except:
            art_source = response_text["source"]

        ## EXTRACT LAT LONG FOR PLACENAME
        url = "https://maps.googleapis.com/maps/api/geocode/json?address=" + placeurl +"&key=" + GPapikey

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

        record = [art_date,art_title,art_vehicles,places,type_land,art_county,latlong,art_source]

        dfA.loc[1] = record
        time.sleep(5)

st.dataframe(dfA, width=800)
def convert_df_to_csv(df):
  return df.to_csv().encode('utf-8')

st.download_button(
  label="Download data as CSV",
  data=convert_df_to_csv(dfA),
  file_name='article_summarys.csv',
  mime='text/csv',
)
