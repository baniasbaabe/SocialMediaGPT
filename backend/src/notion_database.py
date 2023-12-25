from typing import Optional
from notion_client import Client
from langchain import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
import src.prompts as prompts
import ast

class NotionDatabase:

    def __init__(self, notion: Client) -> None:
        self.notion = notion

    def get_templates(self, data: dict) -> dict:
        if not data.databaseId:
            return {"count": 0, "data": []}

        available_templates = self.notion.databases.query(
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
                "content": self.notion.blocks.children.list(template["id"])["results"][0][
                    "paragraph"
                ]["rich_text"][0]["text"]["content"],
            }
            for id, template in enumerate(available_templates)
        ]

        return {"count": len(available_templates), "data": available_templates}

    def create_template(self, data: dict) -> dict:
        database_id = self._create_database(data)

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

        self.notion.pages.create(parent=parent, properties=properties, children=children)

        response = template

        if not data.databaseId:
            response["databaseId"] = database_id

        return response

    def generate_posts(self, data: dict) -> list:
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

            self.notion.pages.create(parent=parent, properties=properties, children=children)

        return posts

    def _create_database(self, data: dict) -> Optional[str]:
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

            database_id = self.notion.databases.create(
                parent=parent, title=title, properties=properties, icon=icon, is_inline=True
            )["id"]

        return database_id