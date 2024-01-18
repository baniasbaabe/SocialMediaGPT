import ast
from typing import Dict, List, Optional

from notion_client import Client

from src.data_models import GeneratePosts, GetTemplates, TemplateCreate
from src.llm import LLM


class NotionDatabase:
    """This class manages the interaction with the Notion Database.

    Parameters:
    - notion (Client): The Notion client.
    - llm (LLM): The LLM instance.

    Methods:
    - get_templates(data: GetTemplates) -> Dict[int, List[Dict[str, str]]]:
        Returns the available templates in the database.
    - create_template(data: TemplateCreate) -> Dict[str, str]: Creates a new template
        and insert it into the database.
    - generate_posts(data: GeneratePosts) -> List[Dict[str, str]]: Generates posts
        from a template and insert them into the database.

    Example:
    ```python
    openai_key = "your_openai_api_key"
    model_name = "your_model_name"
    notion_key = "your_notion_key"
    prompt_template = PromptTemplate.from_template("Your prompt template {}")

    llm = LLM(openai_api_key=openai_key, model_name=model_name, prompt_template=prompt_template)
    generated_text = llm({"placeholder": "value"})

    notion = Client(auth=notion_key)

    notion_database = NotionDatabase(notion, llm)
    templates = notion_database.get_templates()
    ```
    """

    def __init__(self, notion: Client, llm: LLM = None) -> None:
        """Initialize the Notion Database instance.

        Parameters:
         - notion (Client): The Notion client.
        - llm (LLM): The LLM instance.
        """
        self.notion = notion
        self.llm = llm

    def get_templates(self, data: GetTemplates) -> Dict[int, List[Dict[str, str]]]:
        """Returns the available templates in the database.

        Args:
            data (GetTemplates): The data model for getting templates.

        Returns:
            Dict[int, List[Dict[str, str]]]: The available templates in the database.
        """
        if not data.databaseId:
            return {"count": 0, "data": []}

        available_templates = self._query_available_templates(data.databaseId)

        formatted_templates = self._format_templates(available_templates)

        return {"count": len(formatted_templates), "data": formatted_templates}

    def create_template(self, data: TemplateCreate) -> Dict[str, str]:
        """Creates a new template and insert it into the database.

        Args:
            data (TemplateCreate): The data model for creating a template.

        Returns:
            Dict[str, str]: The created template.
        """
        database_id = self._create_database(data)
        template = self._generate_template(data)

        self._store_template_in_notion(
            template, database_id if not data.databaseId else data.databaseId
        )

        response = template

        if not data.databaseId:
            response["databaseId"] = database_id

        return response

    def generate_posts(self, data: GeneratePosts) -> List[Dict[str, str]]:
        """Generates posts from a template and insert them into the database.

        Args:
            data (GeneratePosts): The data model for generating posts.

        Returns:
            List[Dict[str, str]]: The generated posts.
        """
        posts = self._generate_posts(data)

        self._store_generated_posts(posts, data.databaseId)

        return posts

    def _generate_posts(self, data: GeneratePosts) -> List[Dict[str, str]]:
        posts = ast.literal_eval(
            self.llm(
                {
                    "TEMPLATE": data.templateText,
                    "NUMBER_OF_POSTS": data.numPosts,
                    "TOPICS": data.topics,
                }
            )
        )

        return posts

    def _query_available_templates(self, database_id: str) -> List[Dict]:
        return self.notion.databases.query(
            **{
                "database_id": database_id,
                "filter": {
                    "property": "Status",
                    "select": {
                        "equals": "Template",
                    },
                },
            }
        )["results"]

    def _format_templates(self, templates: List[Dict]) -> List[Dict[str, str]]:
        return [
            {
                "id": id,
                "title": template["properties"]["Title"]["title"][0]["text"]["content"],
                "content": self.notion.blocks.children.list(template["id"])["results"][
                    0
                ]["paragraph"]["rich_text"][0]["text"]["content"],
            }
            for id, template in enumerate(templates)
        ]

    def _create_database(self, data: Dict) -> Optional[str]:
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
                parent=parent,
                title=title,
                properties=properties,
                icon=icon,
                is_inline=True,
            )["id"]

        return database_id

    def _generate_template(self, data: TemplateCreate) -> Dict[str, str]:
        template_text = self.llm({"LINKEDIN_POST": data.text})
        return ast.literal_eval(template_text)

    def _store_template_in_notion(
        self, template: Dict[str, str], database_id: str
    ) -> None:
        parent = {"database_id": database_id}
        properties = {
            "title": {
                "title": [{"type": "text", "text": {"content": template["title"]}}]
            },
            "Status": {"select": {"name": "Template"}},
        }
        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": template["post"]}}
                    ]
                },
            }
        ]

        self.notion.pages.create(
            parent=parent, properties=properties, children=children
        )

    def _store_generated_posts(
        self, posts: List[Dict[str, str]], database_id: str
    ) -> None:
        for post in posts:
            parent = {"database_id": database_id}
            properties = {
                "title": {
                    "title": [{"type": "text", "text": {"content": post["title"]}}]
                },
                "Status": {"select": {"name": "Working"}},
            }
            children = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": post["post"]}}
                        ]
                    },
                }
            ]

            self.notion.pages.create(
                parent=parent, properties=properties, children=children
            )
