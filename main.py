from flask import Flask, render_template, request
import pyodbc
import langchain
import requests
import json
import uuid
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.corpus import stopwords
import string
import openai
import os
from dotenv import load_dotenv

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('corpus')
nltk.download('wordnet')

load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect', methods=['POST'])
def connect():
    # Get the form data
    server = request.form['server']
    database = request.form['database']
    username = request.form['username']
    password = request.form['password']
    user_input=request.form["user_input"]
    table = str.maketrans('', '', string.punctuation) # remove punctuation
    #tokens.tokenize(input_prompt)
    tokens = word_tokenize(user_input)  #split into words
    stripped = [w.translate(table) for w in tokens]
    words = [word for word in stripped if word.isalpha()]
    # Stop words
    stop_words = set(stopwords.words('english'))
    words = [w for w in words if not w in stop_words]
# Perform lemmatization on tokens
    lemmatizer = WordNetLemmatizer()
    lemmatized_tokens = [lemmatizer.lemmatize(words) for words in words]

# Conversion of tokens back to sentences

# Convert list of tokens to NLTK text object
    text_final = nltk.Text(lemmatized_tokens)
    # Use the OpenAI API to generate a response
    prompt = f"User: {text_final}\nChatbot:"
    chat_history=[]
    response = openai.Completion.create(
          engine="text-davinci-002",
          prompt=prompt,
          temperature=0.5,
          max_tokens=60,
          top_p=1,
          frequency_penalty=0,
          stop=["\nUser: ","\nChatbot: "]
    )


    # Define the connection string
    driver = '{ODBC Driver 17 for SQL Server}'
    connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"

    # Connect to the database
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        message = "Connected to the database!"
    except Exception as e:
        error_message = langchain.parse_error_message(str(e))
        message = f"Error connecting to the database: {error_message}"
     
    # Read data from the database using Llama Index
    query = "SELECT * FROM my_table"
    payload = {
        "q": query,
        "count": 10,
        "offset": 0,
        "mkt": "en-US",
        "safesearch": "Moderate"
    }
    headers = {
        "Ocp-Apim-Subscription-Key": "YOUR_SUBSCRIPTION_KEY",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    response = requests.get(llama_index_endpoint, headers=headers, params=payload)
    response.raise_for_status()
    data = json.loads(response.content)["webPages"]["value"]

    # Translate the data to English using LLM
    translated_data = []
    for item in data:
        payload = item["snippet"]
        headers = {
            "Ocp-Apim-Subscription-Key": "YOUR_SUBSCRIPTION_KEY",
            "Content-type": "application/json",
            "X-ClientTraceId": str(uuid.uuid4())
        }
        response = requests.post(llm_endpoint, headers=headers, data=payload.encode("utf-8"))
        response.raise_for_status()
        translated_text = response.content.decode("utf-8")
        translated_data.append(translated_text)

    # Use GPT to generate text based on the translated data
    generated_text = []
    for item in translated_data:
        payload = {
            "prompt": item,
            "max_tokens": 50,
            "temperature": 0.7
        }
        response = requests.post(gpt_endpoint, headers=gpt_headers, json=payload)
        response.raise_for_status()
        generated_text.append(json.loads(response.content)["choices"][0]["text"])
    # Extract response from OpenAI API result
    bot_response=response.choices[0].text.strip()
    chat_history.append(f"{text_final}\nchatbot: {bot_response}")

    # Render the result page
    return render_template('response.html', user_input=f"{text_final}", message=message, bot_response=bot_response, generated_text=generated_text)

if __name__ == '__main__':
    # Set up the LLM and Llama Index API endpoints
    llm_endpoint = "https://api.cognitive.microsoft.com/sts/v1.0/issueToken"
    llama_index_endpoint = "https://api.cognitive.microsoft.com/bing/v7.0/search"

    # Set up the GPT API endpoint and authentication headers
    gpt_endpoint = "https://api.openai.com/v1/engines/davinci-codex/completions"
    gpt_headers = {
        "Content-Type": "application/json",
        "Authorization": "openai.api_key"
    }

    app.run(debug=True)
