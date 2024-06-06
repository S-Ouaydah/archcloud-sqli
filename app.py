from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import psycopg2

app = FastAPI()
templates = Jinja2Templates(directory="templates")

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
        'query': query
    }

    return templates.TemplateResponse('login.html', context)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('index.html', {"request": request})
