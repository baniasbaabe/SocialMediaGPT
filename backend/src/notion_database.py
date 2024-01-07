import ast
from typing import Dict, List, Optional

from langchain import PromptTemplate
from notion_client import Client

import src.prompts as prompts
from src.data_models import GeneratePosts, GetTemplates, TemplateCreate
from src.llm import LLM


class NotionDatabase:
    """Notion Database Manager.

    This class facilitates interaction with the Notion database to manage templates and generated posts.

    Parameters:
    - notion (Client): An instance of the Notion API Client.

    Methods:
    - get_templates(data: GetTemplates) -> Dict[str, List[Dict[str, str]]]:
      Retrieves templates from the Notion database based on the provided data.

    - create_template(data: TemplateCreate) -> Dict[str, str]:
      Creates a new template in the Notion database and returns the template details.

    - generate_posts(data: GeneratePosts) -> List[Dict[str, str]]:
      Generates posts using the provided template text and topics, then stores them in the Notion database.

    - _create_database(data: Dict) -> Optional[str]:
      Creates a new database in Notion if it does not exist and returns the database ID.

    Example:
    ```python
    notion_client = Client(api_key="your_notion_api_key")
    notion_db_manager = NotionDatabase(notion=notion_client)

    # Example usage of methods
    templates = notion_db_manager.get_templates(data=GetTemplates(databaseId='your_database_id'))
    new_template = notion_db_manager.create_template(data=TemplateCreate(
        notionKey='your_notion_api_key',
        openaiKey='your_openai_api_key',
        text='your_template_text',
        model='your_model_name',
        databaseId='your_database_id',
        pageId='your_page_id'
    ))
    generated_posts = notion_db_manager.generate_posts(data=GeneratePosts(
        notionKey='your_notion_api_key',
        openaiKey='your_openai_api_key',
        databaseId='your_database_id',
        templateText='your_template_text',
        numPosts=5,
        model='your_model_name',
        topics='your_topics'
    ))
    ```

    Note:
    This class assumes a specific structure of the Notion database and may need adjustments based on your actual database schema.
    """

    def __init__(self, notion: Client) -> None:
        self.notion = notion

    def get_templates(self, data: GetTemplates) -> Dict[int, List[Dict[str, str]]]:
        """Retrieve templates from the Notion database.

        Parameters:
        - data (GetTemplates): Data required for retrieving templates.

        Returns:
        - Dict[str, List[Dict[str, str]]]: A dictionary containing the count and data of retrieved templates.
        """
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
                "content": self.notion.blocks.children.list(template["id"])["results"][
                    0
                ]["paragraph"]["rich_text"][0]["text"]["content"],
            }
            for id, template in enumerate(available_templates)
        ]

        return {"count": len(available_templates), "data": available_templates}

    def create_template(self, data: TemplateCreate) -> Dict[str, str]:
        """Create a new template in the Notion database.

        Parameters:
        - data (TemplateCreate): Data required for creating a new template.

        Returns:
        - Dict[str, str]: A dictionary containing the details of the created template.
        """
        database_id = self._create_database(data)

        templatizing_prompt_template = PromptTemplate.from_template(
            template=prompts.templatizing_prompt
        )

        llm = LLM(
            openai_api_key=data.openaiKey,
            temperature=0,
            model_name=data.model,
            prompt_template=templatizing_prompt_template,
        )

        template = llm({"LINKEDIN_POST": data.text})
        template = ast.literal_eval(template)

        parent = {"database_id": database_id if database_id else data.databaseId}
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

        response = template

        if not data.databaseId:
            response["databaseId"] = database_id

        return response

    def generate_posts(self, data: GeneratePosts) -> List[Dict[str, str]]:
        """Generate posts using a template and store them in the Notion
        database.

        Parameters:
        - data (GeneratePosts): Data required for generating posts.

        Returns:
        - List[Dict[str, str]]: A list of dictionaries containing the details of generated posts.
        """
        creating_posts_prompt_template = PromptTemplate.from_template(
            template=prompts.creating_posts_prompt
        )

        llm = LLM(
            openai_api_key=data.openaiKey,
            temperature=0,
            model_name=data.model,
            prompt_template=creating_posts_prompt_template,
        )

        posts = llm(
            {
                "TEMPLATE": data.templateText,
                "NUMBER_OF_POSTS": data.numPosts,
                "TOPICS": data.topics,
            }
        )

        posts = ast.literal_eval(posts)

        for post in posts:
            parent = {"database_id": data.databaseId}
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

        return posts

    def _create_database(self, data: Dict) -> Optional[str]:
        """Create a new Notion database if it does not exist and return the
        database ID.

        Parameters:
        - data (Dict): Additional data required for creating a new database.

        Returns:
        - Optional[str]: The database ID if created, otherwise None.
        """
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


'''
from typing import Optional, Dict, List
from langchain import PromptTemplate
from notion_client import Client
from src.data_models import GeneratePosts, GetTemplates, TemplateCreate
from src.llm import LLM

class NotionDatabase:
    """
    Notion Database Manager

    This class facilitates interaction with the Notion database to manage templates and generated posts.

    Parameters:
    - notion (Client): An instance of the Notion API Client.

    Methods:
    - get_templates(data: GetTemplates) -> Dict[str, List[Dict[str, str]]]:
      Retrieves templates from the Notion database based on the provided data.

    - create_template(data: TemplateCreate) -> Dict[str, str]:
      Creates a new template in the Notion database and returns the template details.

    - generate_posts(data: GeneratePosts) -> List[Dict[str, str]]:
      Generates posts using the provided template text and topics, then stores them in the Notion database.

    - _create_database(data: Dict) -> Optional[str]:
      Creates a new database in Notion if it does not exist and returns the database ID.

    Example:
    ```python
    notion_client = Client(api_key="your_notion_api_key")
    notion_db_manager = NotionDatabase(notion=notion_client)

    # Example usage of methods
    templates = notion_db_manager.get_templates(data=GetTemplates(databaseId='your_database_id'))
    new_template = notion_db_manager.create_template(data=TemplateCreate(
        notionKey='your_notion_api_key',
        openaiKey='your_openai_api_key',
        text='your_template_text',
        model='your_model_name',
        databaseId='your_database_id',
        pageId='your_page_id'
    ))
    generated_posts = notion_db_manager.generate_posts(data=GeneratePosts(
        notionKey='your_notion_api_key',
        openaiKey='your_openai_api_key',
        databaseId='your_database_id',
        templateText='your_template_text',
        numPosts=5,
        model='your_model_name',
        topics='your_topics'
    ))
    ```

    Note:
    This class assumes a specific structure of the Notion database and may need adjustments based on your actual database schema.
    """

    def __init__(self, notion: Client) -> None:
        """
        Initialize the NotionDatabase instance.

        Parameters:
        - notion (Client): An instance of the Notion API Client.
        """
        self.notion = notion

    def get_templates(self, data: GetTemplates) -> Dict[str, List[Dict[str, str]]]:
        """
        Retrieve templates from the Notion database.

        Parameters:
        - data (GetTemplates): Data required for retrieving templates.

        Returns:
        - Dict[str, List[Dict[str, str]]]: A dictionary containing the count and data of retrieved templates.
        """
        # Implementation details...

    def create_template(self, data: TemplateCreate) -> Dict[str, str]:
        """
        Create a new template in the Notion database.

        Parameters:
        - data (TemplateCreate): Data required for creating a new template.

        Returns:
        - Dict[str, str]: A dictionary containing the details of the created template.
        """
        # Implementation details...

    def generate_posts(self, data: GeneratePosts) -> List[Dict[str, str]]:
        """
        Generate posts using a template and store them in the Notion database.

        Parameters:
        - data (GeneratePosts): Data required for generating posts.

        Returns:
        - List[Dict[str, str]]: A list of dictionaries containing the details of generated posts.
        """
        # Implementation details...

    def _create_database(self, data: Dict) -> Optional[str]:
        """
        Create a new Notion database if it does not exist and return the database ID.

        Parameters:
        - data (Dict): Additional data required for creating a new database.

        Returns:
        - Optional[str]: The database ID if created, otherwise None.
        """
        # Implementation details...

'''
