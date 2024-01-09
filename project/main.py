from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from tasks import create_task, celery_app
from celery.result import AsyncResult

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("dashboard.html", context={"request": request})


@app.get("/create_task", status_code=201)
def run_task(request: Request):
    task = create_task.delay()
    return JSONResponse({"task_id": task.id})


@app.get("/task/{task_id}")
def read_task(task_id: str):
    result = celery_app.AsyncResult(task_id)

    response = {
        'status': result.status,
        'result': result.result
    }

    return response
