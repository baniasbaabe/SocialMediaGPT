import ast
from typing import Optional

import uvicorn
from dotenv import dotenv_values
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from notion_client import Client
from pydantic import BaseModel
import src.prompts as prompts

FRONTEND_ENDPOINT = dotenv_values(".env").get("FRONTEND_ENDPOINT", None)

app = FastAPI(debug=False)

origins = ["http://localhost:3000", "localhost:3000", FRONTEND_ENDPOINT]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TemplateCreate(BaseModel):
    notionKey: str
    openaiKey: str
    text: str
    model: str
    databaseId: Optional[str] = None
    pageId: Optional[str] = None


class GeneratePosts(BaseModel):
    notionKey: str
    openaiKey: str
    databaseId: str
    templateText: str
    numPosts: int
    model: str
    topics: str


class GetTemplates(BaseModel):
    notionKey: str
    databaseId: str


@app.post("/create_template")
async def create_template(data: TemplateCreate):
    notion = Client(auth=data.notionKey)
    database_id = None
    if not data.databaseId:
        properties = {
            "Title": {"title": {}},
            "Status": {
                "name": "status",
                "type": "select",
                "select": {
                    "options": [
                        {"name": "Template", "color": "blue"},
                        {"name": "Working", "color": "yellow"},
                        {"name": "Done", "color": "red"},
                    ]
                },
            },
        }

        title = [
            {
                "type": "text",
                "text": {"content": "LinkedIn Posts (Powered by SocialMediaGPT)"},
            }
        ]
        icon = {"type": "emoji", "emoji": "🤖"}
        parent = {"type": "page_id", "page_id": data.pageId}

        database_id = notion.databases.create(
            parent=parent, title=title, properties=properties, icon=icon, is_inline=True
        )["id"]

    llm = ChatOpenAI(
        openai_api_key=data.openaiKey,
        temperature=0,
        model_name=data.model,
    )

    templatizing_prompt_template = PromptTemplate.from_template(
        template=prompts.templatizing_prompt
    )

    llm_chain = LLMChain(llm=llm, prompt=templatizing_prompt_template)

    template = llm_chain(data.text)["text"]

    template = ast.literal_eval(template)

    parent = {"database_id": database_id if database_id else data.databaseId}
    properties = {
        "title": {"title": [{"type": "text", "text": {"content": template["title"]}}]},
        "Status": {"select": {"name": "Template"}},
    }
    children = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": template["post"]}}]
            },
        }
    ]

    notion.pages.create(parent=parent, properties=properties, children=children)

    response = template

    if not data.databaseId:
        response["databaseId"] = database_id

    # response = {"title": "Title of Create templateaaaaaa", "post": "Post of Create template"}
    # if not data.databaseId:
    #     response["databaseId"] = 653

    return response


@app.post(
    "/get_templates",
)
async def get_templates(data: GetTemplates):
    if not data.databaseId:
        return {"count": 0, "data": []}
    notion = Client(auth=data.notionKey)
    available_templates = notion.databases.query(
        **{
            "database_id": data.databaseId,
            "filter": {
                "property": "Status",
                "select": {
                    "equals": "Template",
                },
            },
        }
    )["results"]

    available_templates = [
        {
            "id": id,
            "title": template["properties"]["Title"]["title"][0]["text"]["content"],
            "content": notion.blocks.children.list(template["id"])["results"][0][
                "paragraph"
            ]["rich_text"][0]["text"]["content"],
        }
        for id, template in enumerate(available_templates)
    ]
    # available_templates = {"count": 3, data: [{"id": 1, "title": "Title of template", "content": "Content of template" + str(random.randint(1,100))}, {"id": 2, "title": "Title of template 2", "content": "Content of template 2"}]}
    # return available_templates
    return {"count": len(available_templates), "data": available_templates}


@app.post(
    "/generate_posts",
)
async def generate_posts(data: GeneratePosts):
    notion = Client(auth=data.notionKey)
    llm = ChatOpenAI(
        openai_api_key=data.openaiKey, temperature=0, model_name=data.model
    )


    creating_posts_prompt_template = PromptTemplate.from_template(
        template=prompts.creating_posts_prompt
    )

    llm_chain = LLMChain(llm=llm, prompt=creating_posts_prompt_template)

    posts = llm_chain(
        {
            "TEMPLATE": data.templateText,
            "NUMBER_OF_POSTS": data.numPosts,
            "TOPICS": data.topics,
        }
    )["text"]

    posts = ast.literal_eval(posts)

    for post in posts:
        parent = {"database_id": data.databaseId}
        properties = {
            "title": {"title": [{"type": "text", "text": {"content": post["title"]}}]},
            "Status": {"select": {"name": "Working"}},
        }
        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": post["post"]}}]
                },
            }
        ]

        notion.pages.create(parent=parent, properties=properties, children=children)
    return posts


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
