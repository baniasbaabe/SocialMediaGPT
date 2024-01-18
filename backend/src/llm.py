from typing import Any, Dict

from langchain import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI


# TODO: Change sync to async call for LLM
class LLM:
    """This class manages the interaction with a language model using OpenAI's
    Chat API.

    Parameters:
    - openai_api_key (str): The API key for accessing the OpenAI API.
    - model_name (str): The name of the language model.
    - prompt_template (PromptTemplate): A template for constructing prompts.
    - temperature (float, optional): Controls the randomness of the model's output.
      Higher values (e.g., 0.8) make the output more random. Defaults to 0.0.

    Attributes:
    - llm (ChatOpenAI): An instance of ChatOpenAI for interacting with the
    OpenAI Chat API.
    - prompt_template (PromptTemplate): The provided template for constructing
    prompts.
    - llm_chain (LLMChain): An instance of LLMChain for managing the language
    model chain.

    Methods:
    - __call__(placeholder_mapping: Dict[str, Any]) -> str:
      Generates text using the language model chain based on the
      provided placeholder mapping.

    Example:
    ```python
    openai_key = "your_openai_api_key"
    model_name = "your_model_name"
    prompt_template = PromptTemplate.from_template("Your prompt template {}")

    llm = LLM(openai_api_key=openai_key, model_name=model_name, prompt_template=prompt_template)
    generated_text = llm({"placeholder": "value"})
    ```

    Note:
    The `__call__` method is the primary interface for generating
    text using the language model chain.
    """

    def __init__(
        self,
        openai_api_key: str,
        model_name: str,
        prompt_template: PromptTemplate,
        temperature: float = 0.0,
    ) -> None:
        """Initialize the LLM instance.

        Parameters:
        - openai_api_key (str): The API key for accessing the OpenAI API.
        - model_name (str): The name of the language model.
        - prompt_template (PromptTemplate): A template for constructing prompts.
        - temperature (float, optional): Controls the randomness of the model's output.
          Higher values (e.g., 0.8) make the output more random. Defaults to 0.0.
        """

        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            temperature=temperature,
            model_name=model_name,
        )
        self.prompt_template = prompt_template
        self.llm_chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

    def __call__(self, placeholder_mapping: Dict[str, Any]) -> str:
        """Generate text using the language model chain based on the provided
        placeholder mapping.

        Parameters:
        - placeholder_mapping (Dict[str, Any]): A mapping of placeholders to their
        corresponding values.

        Returns:
        - str: The generated text.
        """
        return self.llm_chain(placeholder_mapping)["text"]
