import pytest
from unittest.mock import patch, MagicMock
from notion_client import Client
from src.notion_database import NotionDatabase, GetTemplates

@pytest.fixture
def notion_instance():
    notion_client_mock = MagicMock(spec=Client)
    notion_client_mock.databases = MagicMock()
    notion_client_mock.blocks = MagicMock()
    return notion_client_mock

def test_get_templates(notion_instance):
    notion_db = NotionDatabase(notion=notion_instance)

    with patch.object(notion_instance.databases, 'query') as mock_query, \
         patch.object(notion_instance.blocks.children, 'list') as mock_blocks_list:
         
        mock_query.return_value = {"results": [{"id": "template_id", "properties": {"Title": {"title": [{"text": {"content": "Template 1"}}]}}}]}

        mock_blocks_list.return_value = {
            "results": [{"paragraph": {"rich_text": [{"text": {"content": "Template content"}}]}}]
        }

        result = notion_db.get_templates(data=GetTemplates(notionKey="notionkey", databaseId='databaseid'))
        
        assert result == {'count': 1, 'data': [{'id': 0, 'title': 'Template 1', 'content': 'Template content'}]}

        mock_query.assert_called_once_with(database_id='databaseid', filter={
            'property': 'Status',
            'select': {'equals': 'Template'}
        })
