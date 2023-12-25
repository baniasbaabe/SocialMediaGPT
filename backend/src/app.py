import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from notion_client import Client

from src.data_models import GeneratePosts, GetTemplates, TemplateCreate
from src.notion_database import NotionDatabase

load_dotenv()

FRONTEND_ENDPOINT = os.getenv("FRONTEND_ENDPOINT")

app = FastAPI(debug=False)

origins = ["http://localhost:3000", "localhost:3000", FRONTEND_ENDPOINT]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/create_template")
async def create_template(data: TemplateCreate):
    notion = Client(auth=data.notionKey)
    notion_db = NotionDatabase(notion)
    response = notion_db.create_template(data)

    return response


@app.post(
    "/get_templates",
)
async def get_templates(data: GetTemplates):
    notion = Client(auth=data.notionKey)
    notion_db = NotionDatabase(notion)
    response = notion_db.get_templates(data)

    return response


@app.post(
    "/generate_posts",
)
async def generate_posts(data: GeneratePosts):
    notion = Client(auth=data.notionKey)
    notion_db = NotionDatabase(notion)
    response = notion_db.generate_posts(data)

    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
