import os
import re
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from app.db.database import (
    init_db, seed_db,
    insert_test, get_all_tests,
    get_stats, get_daily, get_stats_for_date,
)
from app.models.schemas import TestCreate, ChatRequest
from app.chat import openai_chat, rule_based_chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_db()
    yield


app = FastAPI(
    title="Yield Monitor API",
    description="Manual testing yield tracking dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.svg", media_type="image/svg+xml")


@app.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
async def chrome_devtools():
    from fastapi.responses import JSONResponse
    return JSONResponse(content={})


@app.get("/script", include_in_schema=False)
async def view_script():
    return FileResponse("tests/test_yield.py", media_type="text/plain")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/tests", status_code=201)
async def create_test(payload: TestCreate):
    new_id = insert_test(
        serial_number=payload.serial_number,
        part_number=payload.part_number,
        status=payload.status,
    )
    return {"id": new_id, "message": "Test record created"}


@app.get("/tests")
async def list_tests():
    return get_all_tests()


@app.get("/stats")
async def stats():
    return get_stats()


@app.get("/daily")
async def daily():
    return get_daily()


@app.get("/stats/daily")
async def stats_for_date(date: str):
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD")
    return get_stats_for_date(date)


@app.post("/chat")
async def chat(payload: ChatRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question must not be empty")

    stats_data = get_stats()
    daily_data = get_daily()
    history = [{"role": m.role, "content": m.content} for m in payload.history]

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if api_key:
        answer = await openai_chat(question, stats_data, daily_data, api_key, history)
    else:
        answer = rule_based_chat(question, stats_data, daily_data)

    return {"answer": answer}
