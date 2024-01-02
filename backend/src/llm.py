from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI

class LLM:
    
    def __init__(self, openai_api_key, model_name, prompt_template, temperature=0.0) -> None:
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            temperature=temperature,
            model_name=model_name,
        )
        self.prompt_template = prompt_template
        self.llm_chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
        
    def __call__(self, placeholder_mapping):
        return self.llm_chain(placeholder_mapping)["text"]