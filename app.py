from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from dotenv import load_dotenv
import os
import requests
import psycopg2
import joblib

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
app = FastAPI()
templates = Jinja2Templates(directory="templates")

vectorizer = joblib.load('./vectorizer.pkl')
logistic = joblib.load('./logistic_model.pkl')

def predict(text):
    text_vector = vectorizer.transform([text])
    return bool(int(logistic.predict(text_vector)[0]))
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

@app.post("/login",response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Failed to connect to the database")

    cur = conn.cursor()
    query = f"SELECT * FROM users WHERE username ='{username}' AND password = '{password}'"
    print(query)
    cur.execute(query)
    # cur.execute(query, (username, password))
    user = cur.fetchone()

    cur.close()
    conn.close()

    context = {
        'request': request,
        'success': bool(user),
        'message': 'Logged in successfully!' if user else 'Failed to login!',
        'query': query,
        'logistic_result': predict(query),
        'openai_result': openai_predict(query)
    }

    return templates.TemplateResponse('login.html', context)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('index.html', {"request": request})
