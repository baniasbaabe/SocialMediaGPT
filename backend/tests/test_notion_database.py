from unittest.mock import MagicMock, patch

import pytest
from notion_client import Client

from src.data_models import GeneratePosts, GetTemplates, TemplateCreate
from src.notion_database import NotionDatabase


@pytest.fixture
def mock_notion_client():
    return MagicMock(spec=Client)


@pytest.fixture
def mock_llm():
    def llm_callable(*args, **kwargs):
        llm_instance = MagicMock()
        return llm_instance

    with patch("src.llm.LLM", side_effect=llm_callable) as mock:
        yield mock


def test_get_templates(mock_notion_client):
    notion_db = NotionDatabase(notion=mock_notion_client)

    with patch.object(
        notion_db, "_query_available_templates"
    ) as mock_query, patch.object(
        notion_db, "_format_templates"
    ) as mock_format_templates:
        mock_query.return_value = [
            {
                "id": "template_id",
                "properties": {
                    "Title": {"title": [{"text": {"content": "Template 1"}}]}
                },
            }
        ]
        mock_format_templates.return_value = [
            {"id": 0, "title": "Template 1", "content": "Template content"}
        ]

        result = notion_db.get_templates(
            data=GetTemplates(notionKey="notionkey", databaseId="databaseid")
        )

        assert result == {
            "count": 1,
            "data": [{"id": 0, "title": "Template 1", "content": "Template content"}],
        }

        mock_query.assert_called_once_with("databaseid")
        mock_format_templates.assert_called_once_with(
            [
                {
                    "id": "template_id",
                    "properties": {
                        "Title": {"title": [{"text": {"content": "Template 1"}}]}
                    },
                }
            ]
        )


def test_create_template(mock_notion_client, mock_llm):
    notion_db = NotionDatabase(notion=mock_notion_client, llm=mock_llm)
    data = TemplateCreate(
        notionKey="notionkey",
        openaiKey="openaikey",
        text="template_text",
        model="model_name",
        pageId="pageid",
    )

    with patch.object(notion_db, "_create_database") as mock_create_db, patch.object(
        notion_db, "_generate_template"
    ) as mock_generate_template, patch.object(
        notion_db, "_store_template_in_notion"
    ) as mock_store_template_in_notion:
        mock_create_db.return_value = "created_database_id"
        mock_generate_template.return_value = {
            "title": "Template 1",
            "post": "Template content",
        }

        result = notion_db.create_template(data=data)

        assert result == {
            "title": "Template 1",
            "post": "Template content",
            "databaseId": "created_database_id",
        }

        mock_create_db.assert_called_once_with(data)

        mock_generate_template.assert_called_once_with(data)

        mock_store_template_in_notion.assert_called_once_with(
            {
                "title": "Template 1",
                "post": "Template content",
                "databaseId": "created_database_id",
            },
            "created_database_id",
        )


def test_generate_posts(mock_notion_client, mock_llm):
    # Arrange
    notion_db = NotionDatabase(notion=mock_notion_client, llm=mock_llm)

    data = GeneratePosts(
        notionKey="notionkey",
        openaiKey="openaikey",
        databaseId="databaseid",
        templateText="template_text",
        numPosts=5,
        model="model_name",
        topics="topics",
    )

    # Act
    with patch.object(
        notion_db, "_store_generated_posts"
    ) as mock_store_generated_posts, patch.object(
        notion_db, "_generate_posts"
    ) as mock_generate_posts:
        mock_generate_posts.return_value = [
            {"title": "Short Title of the post", "post": "The post you made"},
            {"title": "Another short title", "post": "Another post you made"},
        ]

        _ = notion_db.generate_posts(data)

    mock_store_generated_posts.assert_called_once_with(
        [
            {"title": "Short Title of the post", "post": "The post you made"},
            {"title": "Another short title", "post": "Another post you made"},
        ],
        "databaseid",
    )

    mock_generate_posts.assert_called_once_with(data)
