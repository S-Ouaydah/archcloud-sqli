import os
import psycopg2
import joblib

from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()
app = FastAPI()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
templates = Jinja2Templates(directory="templates")

vectorizer = joblib.load('./combined_vectorizer.pkl')
logistic = joblib.load('./logistic_model.pkl')
random_forest = joblib.load('./randomforest_model.pkl')  # Load the Random Forest model

def predict_logistic(text):
    text_vector = vectorizer.transform([text])
    return bool(int(logistic.predict(text_vector)[0]))

def predict_random_forest(text):
    text_vector = vectorizer.transform([text])
    return bool(int(random_forest.predict(text_vector)[0]))

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname='archcloud',
            user='',
            password='',
            host='localhost'
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def openai_predict(text):
    openai = OpenAI(api_key=OPENAI_API_KEY)
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an experienced sql injection detector. You will ONLY EVER reply by 0 or 1. 0 means the query is not an injection, 1 means the query is an injection."},
            {"role": "user", "content": text}
        ]
    )
    if response.choices[0].message.content not in ['0', '1']:
        raise ValueError("Invalid response from OpenAI")
    print(response.choices[0].message.content)
    return bool(int(response.choices[0].message.content))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('index.html', {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Failed to connect to the database")

    cur = conn.cursor()
    query = f"SELECT * FROM users WHERE username ='{username}' AND password = '{password}'"
    # parameterized query
    param_query = "SELECT * FROM users WHERE username = %s AND password = %s"
    # print(query)
    # cur.execute(query)
    cur.execute(param_query, (username, password))
    user = cur.fetchone()

    cur.close()
    conn.close()

    context = {
        'request': request,
        'success': bool(user),
        'message': 'Logged in successfully!' if user else 'Failed to login!',
        'query': query,
        'logistic_result': predict_logistic(query),
        'random_forest_result': predict_random_forest(query),  # Add Random Forest result
        'openai_result': openai_predict(query)
    }

    return templates.TemplateResponse('login.html', context)

