import os

from langchain import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from notion_client import Client

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

notion = Client(auth=os.getenv("NOTION_TOKEN"))

# Create database where LinkedIn posts will be stored

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
        "text": {"content": "LinkedIn Posts Template (Powered by SocialMediaGPT)"},
    }
]
icon = {"type": "emoji", "emoji": "🤖"}
parent = {"type": "page_id", "page_id": os.getenv("NOTION_PAGE_ID")}

notion.databases.create(
    parent=parent, title=title, properties=properties, icon=icon, is_inline=True
)

llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")

templatizing_prompt = """
You are GPT-Template, a program that turns LinkedIn Posts into perfectly usable templates. \
A template is a piece of content with the right formatting & post structure, with bracket like "[]" filled with the best indication for the writer \
to make it its own piece of text. Here is an example. The original LinkedIn post between '':\n'The 9 to 5 is getting pummeled.\nThe great resignation is growing faster than ever.\nAnd I love it.\nWhy?\nBecause the workforce is tired...'\
The template GPT-Template should provide between '':'The [issue/topic] is [massive change]\nThe [trend] is [intensifying].\nAnd I [strong emotion] it.\nWhy?\nBecause [target audience] are [strong negative emotion].'\
Here's another LinkedIn post example between '': 'I quit my job.\nIt was the biggest salary I ever made in my life.\nMy personal income went to $0.\nI threw away 66% of my belongings.'\
Here's what GPT-Template should answer between '':'I [significant decision or action].\nIt was the [notable achievement] in my [context].\nMy [personal consequence or change].\nI [action taken] of my [posessions or attachments].'.\n\
Now, I will give you a LinkedIn posts. I want you to generate only the reusable template. The template should be generic and used on any topic. I want it to look less like of a post but more like a template anyone could use. The output should have the following \
dictionary format in minimized form (no spaces, ideally one line): {{"title": "Short title of template", "post": "The template you made"}} Please do your best, this is important to my career. \
I'm going to tip you $200 for a perfect response.\
This is the LinkedIn post: '{LINKEDIN_POST}'.
"""

templatizing_prompt_template = PromptTemplate.from_template(
    template=templatizing_prompt
)

llm_chain = LLMChain(llm=llm, prompt=templatizing_prompt_template)

template = llm_chain(
    "Canva doesn't make you a designer. Ahrefs doesn't make you an SEO expert. Buffer doesn't make you a social media guru. Too many people have tools and call themselves experts without putting in the years of work. Too many companies see tools as replacements for expertise and wonder why they see no results. Tools are simply that, tools. Without the right thinking, they're useless. With the right thinking, they're enhancing."
)["text"]

template = eval(template)

# Create template in notion database
notion.pages.create(
    parent={"database_id": os.getenv("NOTION_DATABASE_ID")},
    properties={
        "Title": {"title": [{"text": {"content": template["title"]}}]},
        # "Status": {"select": {"name": "Template"}},
    },
    children=[
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": template["post"]}}]
            },
        }
    ],
)

creating_posts_prompt = """
You are a viral Content creator. You will take a template and a topic, and generate posts from it. Here is the template between '': \
''{TEMPLATE}'' \
Based on this template, generate {NUMBER_OF_POSTS} different posts where you will only fill in the brackets. The posts should be around the topics {TOPICS}.\
Please use the following output format where you will output a list of dictionaries in minimized form (no spaces, ideally one line): [{{"title": "Short Title of the post", "post": "The post you made"}}, {{"title": "Another short title", "post": "Another post you made"}}] \
Please do your best, this is important to my career. I'm going to tip you $200 for a perfect response.
"""

creating_posts_prompt_template = PromptTemplate.from_template(
    template=creating_posts_prompt
)

llm_chain = LLMChain(llm=llm, prompt=creating_posts_prompt_template)

posts = llm_chain(
    {
        "TEMPLATE": "The [tool/platform] doesn't make you a [profession/skill]. [Too many people/companies] have [tool/platform] and call themselves\
 [profession/expertise] without putting in the [time/effort]. [Too many people/companies] see [tool/platform] as replacements \
 for [knowledge/experience] and wonder why they see no [outcome/results]. [Tools/platforms] are simply that, tools. Without the right \
 [mindset/approach], they're useless. With the right [mindset/approach], they're enhancing."
        "",
        "NUMBER_OF_POSTS": 5,
        "TOPICS": "machine learning, python, and data science",
    }
)["text"]

posts = eval(posts)

# Create entry in notion database

for post in posts:
    notion.pages.create(
        parent={"database_id": os.getenv("NOTION_DATABASE_ID")},
        properties={
            "Title": {"title": [{"text": {"content": post["title"]}}]},
            "Status": {"select": {"name": "Working"}},
        },
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": post["post"]}}]
                },
            }
        ],
    )
