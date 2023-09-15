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

dfACols = {'date': [],'title': [],'vehicles': [], 'place': [],  'county': [], 'latlong': []}
dfA = pd.DataFrame(data = dfACols)

if submit_button and user_input is not None:

        article = user_input.replace('\n', ' ')

        messages=[
                {"role": "system", "content": "You are a news analyst who extracts and summarises news articles. You extract 6 different pieces\
                of content from a provided news article and structure them in the following format including the field name exactly as specified ( \
                date: the data of the incident, if not present use the date 14/09/2023, \
                title: a suggested article title of around 10 words, \
                vehicles: the number of caravans or vehicles if mentioned displayed solely as an integer, \
                place: the primary geographical place to which the article refers,\
                county: the UK county in which the location sits if you can infer that from the location, \
                source: the src URL if given)"},
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
        pattern = r'date: (.*?)title:'
        match = re.findall(pattern, response_text)
        art_date = match[0]
            
        ## TITLE
        pattern = r'title: (.*?)vehicles:'
        match = re.findall(pattern, response_text)
        art_title = match[0]
        
        ## VEHICLES
        pattern = r'vehicles: (.*?)place:'
        match = re.findall(pattern, response_text)
        art_vehicles = match[0]

        ## COUNTY
        pattern = r'county: (.*?)source:'
        match = re.findall(pattern, response_text)
        art_county = match[0]

        ## PLACE
        pattern = r'place: (.*)county:'
        match = re.findall(pattern, response_text)
        places = match[0]
        placeurl = quote(places)

        ##SOURCE
        pattern = r'source: (.*)'
        match = re.findall(pattern, response_text)
        art_source = match[0]

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
                except:
                    lat = "not found"

                try:
                    long = extract_values(data,"lng")
                    long = str(long[0])
                except:
                    long = "not found"

                latlong = lat + ", " + long

        record = [art_date,art_title,art_vehicles,places,art_county,latlong,art_source]

        dfA.loc[len(dfA)] = record
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
