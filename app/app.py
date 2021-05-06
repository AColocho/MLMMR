from collections import Counter
import streamlit as st
from spacy.symbols import ORTH
import spacy
import pickle
import boto3
from datetime import date as dt
import os

@st.cache
def load_app_data():
    path = os.path.dirname(__file__)
    features = pickle.load(open(path+'/features.pkl','rb'))
    model = pickle.load(open(path+'/mlm_model.sv','rb'))
    return features, model

features, model = load_app_data()

def vectorize(data,features):
    counted_data = Counter(data)
    vector = []
    for word in features:
        counted_word = counted_data.get(word,0)
        vector.append(counted_word)
    
    return [vector]

def clean_text(data):
    nlp = spacy.load('en_core_web_sm')
    special_case = [{ORTH: "e-commerce"}]
    nlp.tokenizer.add_special_case("e-commerce", special_case)
    
    text = nlp(data)
        
    temp_data = []
    for word in text:
        if not word.is_stop and not word.is_punct and str(word) != '\xa0':
            if (str(word) == 'entrepreneurial') or (str(word) == 'entrepreneurship'):
                temp_data.append('entrepreneur')
            else:
                temp_data.append(str.lower(word.lemma_))
    
                        
    return temp_data

def update_db_data(new_text_data):
    date = str(dt.today())
    dynamodb = boto3.resource('dynamodb',region_name=os.environ.get('AWS_DEFAULT_REGION'))
    table = dynamodb.Table('MLMMR')
    try:
        response = table.get_item(Key={'data':date})
        text_data = response['Item']['text_data']
        text_data.append(new_text_data)
        item = {'data':date,'text_data':text_data}
        table.put_item(Item=item)
    except:
        item = {'data':date,'text_item':[new_text_data]}
        table.put_item(Item=item)

st.write()
"""
# Multi Level Marketing Message Recognizer (MLMMR)
This app is powered by a machine learning model that classifies messages into MLM or non-MLM. You can find more info about it [here](https://github.com/AColocho/MLMMR)
With more data, we are trying to expand this app to be a helpful tool into classifying potential job recruiting scam messages.

Enter your message in the space below to run it through the model.
"""
contribute_data = st.checkbox('Contribute data to train model. Be sure it does not contain sensitive data.', value= True)

user_data = st.text_area(' ')
clean_user_data = clean_text(user_data)
vectorize_data = vectorize(clean_user_data, features)
prediction = model.predict(vectorize_data)

if user_data:
    if bool(prediction):
        result_message = 'This text is likely a MLM recruiting message.'
    else:
        result_message = 'This text is unlikely a MLM recruiting message.'
else:
    result_message = ''

f"""
{result_message}

Please keep in mind that we did not use a lot of data to train the model, so it is biased towards messages being MLM recruiting messages.
"""

if contribute_data:
    update_db_data(user_data)
