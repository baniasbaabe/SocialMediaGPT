from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from notion_client import Client
from pydantic import BaseModel

app = FastAPI()

origins = ["http://localhost:3000", "localhost:3000"]


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

    templatizing_prompt = """
    You are GPT-Template, a program that turns LinkedIn Posts into perfectly usable templates. \
    A template is a piece of content with the right formatting & post structure, with bracket like "[]" filled with the best indication for the writer \
    to make it its own piece of text. Here is an example. The original LinkedIn post between '':\n'The 9 to 5 is getting pummeled.\nThe great resignation is growing faster than ever.\nAnd I love it.\nWhy?\nBecause the workforce is tired...'\
    The template GPT-Template should provide between '':'The [issue/topic] is [massive change]\nThe [trend] is [intensifying].\nAnd I [strong emotion] it.\nWhy?\nBecause [target audience] are [strong negative emotion].'\
    Here's another LinkedIn post example between '': 'I quit my job.\nIt was the biggest salary I ever made in my life.\nMy personal income went to $0.\nI threw away 66% of my belongings.'\
    Here's what GPT-Template should answer between '':'I [significant decision or action].\nIt was the [notable achievement] in my [context].\nMy [personal consequence or change].\nI [action taken] of my [posessions or attachments].'.\n\
    Now, I will give you a LinkedIn posts. I want you to generate only the reusable template. The template should be generic and used on any topic. The template should use the same formatting, that means the same spaces and enters.\
    I want it to look less like of a post but more like a template anyone could use. The output should have the following \
    dictionary format in minimized form (no spaces, ideally one line): {{"title": "Short title of template", "post": "The template you made"}} Please do your best, this is important to my career. \
    I'm going to tip you $200 for a perfect response.\
    This is the LinkedIn post: '{LINKEDIN_POST}'.
    """

    templatizing_prompt_template = PromptTemplate.from_template(
        template=templatizing_prompt
    )

    llm_chain = LLMChain(llm=llm, prompt=templatizing_prompt_template)

    template = llm_chain(data.text)["text"]

    template = eval(template)

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

    # response = {"title": "Title of Create templateaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" + str(random.randint(1,100)), "post": "Post of Create template"}
    # if not data.databaseId:
    #     response["databaseId"] = str(random.randint(1,100))

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

    creating_posts_prompt = """
    You are a viral Content creator. You will take a template and a topic, and generate posts from it. Here is the template between '': \
    '{TEMPLATE}' \
    Based on this template, generate {NUMBER_OF_POSTS} different posts where you will only fill in the brackets. The posts should be around the topics {TOPICS}.\
    Please use the following output format where you will output a list of dictionaries in minimized form (no spaces, ideally one line):\
    [{{"title": "Short Title of the post", "post": "The post you made"}}, {{"title": "Another short title", "post": "Another post you made"}}] \
    Please do your best, this is important to my career. I'm going to tip you $200 for a perfect response.
    """

    creating_posts_prompt_template = PromptTemplate.from_template(
        template=creating_posts_prompt
    )

    llm_chain = LLMChain(llm=llm, prompt=creating_posts_prompt_template)

    posts = llm_chain(
        {
            "TEMPLATE": data.templateText,
            #         "TEMPLATE": "The [tool/platform] doesn't make you a [profession/skill]. [Too many people/companies] have [tool/platform] and call themselves\
            #  [profession/expertise] without putting in the [time/effort]. [Too many people/companies] see [tool/platform] as replacements \
            #  for [knowledge/experience] and wonder why they see no [outcome/results]. [Tools/platforms] are simply that, tools. Without the right \
            #  [mindset/approach], they're useless. With the right [mindset/approach], they're enhancing.",
            "NUMBER_OF_POSTS": data.numPosts,
            "TOPICS": data.topics,
        }
    )["text"]

    posts = eval(posts)

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
