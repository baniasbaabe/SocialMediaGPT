from unittest.mock import patch

from langchain import PromptTemplate

from src.llm import LLM


def test_llm_call():
    with patch("src.llm.ChatOpenAI") as mock_chat_openai, patch(
        "src.llm.LLMChain"
    ) as mock_llm_chain:
        prompt_template = PromptTemplate.from_template("your_template")

        mock_chat_openai_instance = mock_chat_openai.return_value
        mock_llm_chain_instance = mock_llm_chain.return_value

        mock_llm_chain_instance.return_value = {"text": "Generated response"}

        llm_instance = LLM(
            openai_api_key="your_openai_key",
            model_name="your_model",
            prompt_template=prompt_template,
        )

        result = llm_instance({"placeholder_mapping": "some_data"})

        assert result == "Generated response"

        mock_chat_openai.assert_called_once_with(
            openai_api_key="your_openai_key", temperature=0.0, model_name="your_model"
        )
        mock_llm_chain.assert_called_once_with(
            llm=mock_chat_openai_instance,
            prompt=prompt_template,
        )
        mock_llm_chain_instance.assert_called_once_with(
            {"placeholder_mapping": "some_data"}
        )
