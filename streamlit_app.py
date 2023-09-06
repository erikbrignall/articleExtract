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
st.write('Upload the CSv containing the article list with each article as an individual text field in column 1')
filename = st.file_uploader('Upload a CSV file', type=['csv'])

dfACols = {'title': [],'summary': [],'location': [], 'latlong': []}
dfA = pd.DataFrame(data = dfACols)

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



if uploaded_file is not None:

    #filename = "example_articles.csv"
    dfArt = pd.read_csv(filename)
    article_list = dfArt['article']

    for article in article_list:
        article = article.replace('\n', ' ')

        messages=[
                {"role": "system", "content": "You are a news analyst who extracts and summarises news articles. You extract 3 different pieces of content from a provided news article and structure them in the format: title: a suggested article title of around 6-10 words, summary: a 20 word summary of the article, places: the primary geographical place to which the article refers"},
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

        # extract individual elements from response

        ## TITLE
        pattern = r'title: (.*?)summary:'
        match = re.findall(pattern, response_text)
        art_title = match[0]

        ## SUMMARY
        pattern = r'summary: (.*?)places:'
        match = re.findall(pattern, response_text)
        art_summary = match[0]

        ## PLACES
        pattern = r'places: (.*)'
        match = re.findall(pattern, response_text)
        places = match[0]
        placeurl = quote(places)

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

        record = [art_title,art_summary,places,latlong]

        dfA.loc[len(dfA)] = record
        time.sleep(5)

st.dataframe(dfA, width=800)