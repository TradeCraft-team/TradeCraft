import os
import random
from typing import Literal, Optional
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
class LLMFactory:
    """
    AzureOpenAI:
        gpt-35-turbo-0125
        gpt-4o-mini-2024-07-18
        gpt-4-turbo-2024-04-09
        gpt-4o-2024-08-06
    """
    def __new__(
        cls,
        model: str = 'gpt-4o-2024-08-06',
        provider: Literal['azure_openai', 'openai', 'gemini', 'claude', 'deepseek'] = 'azure_openai',
        api_key: Optional[str] = None,
        api_version: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        temperature: float = 0.,
        **kwargs
    ):
        if provider == 'azure_openai':
            # http://infra.pages.mybigai.ac.cn/tonggpt/
            region_mapping = {
                'gpt-35-turbo-0125': ['canadaeast', 'northcentralus', 'southcentralus'],
                'gpt-4o-mini-2024-07-18': ['eastus'],
                'gpt-4-turbo-2024-04-09': ['eastus2', 'swedencentral'],
                # gpt4v
                'gpt-4-turbo-2024-04-09': ['eastus2', 'swedencentral'],
                # 'gpt-4o-2024-08-06': ['eastus', 'eastus2', 'northcentralus', 'southcentralus', 
                #                       'swedencentral', 'westus', 'westus3'],
                # 'gpt-4o-2024-08-06': ['eastus'],
                'gpt-4o-2024-08-06': ['northcentralus'],
            }
            if model in region_mapping:
                region = random.choice(region_mapping[model])
            else:
                region = os.environ['BIGAI_REGION']

            return AzureChatOpenAI(
                model=model,
                temperature=temperature,
                # api_key=api_key or os.environ['BIGAI_OAI_API_KEY'],
                api_key="",
                # api_version=api_version or os.environ['BIGAI_API_VERSION'],
                api_version="2025-03-01-preview",
                # azure_endpoint=azure_endpoint or f"{os.environ['BIGAI_API_BASE']}/{region}",
                azure_endpoint="https://api.tonggpt.mybigai.ac.cn/proxy/eastus",
                streaming=False,
                **kwargs
            )
        elif provider == 'openai':
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=api_key,
                streaming=False,
                **kwargs
            )
        elif provider == 'gemini':
            return ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                api_key=api_key,
                streaming=False,
                **kwargs
            )
        elif provider == 'claude':
            return ChatAnthropic(
                model=model,
                temperature=temperature,
                api_key=api_key,
                streaming=False,
                **kwargs
            )
        elif provider == 'deepseek':
            return ChatOpenAI(
                model="deepseek-chat",
                temperature=temperature,
                api_key="",
                streaming=False,
                base_url="https://api.deepseek.com/v1",
                **kwargs
            )      
        else:
            raise ValueError(f"Unsupported provider: {provider}")

if __name__ == '__main__':

    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())

    llm = LLMFactory(model='gpt-3.5-turbo', provider='openai', temperature=0.)

    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.messages import HumanMessage
    from langchain_core.prompts import ChatPromptTemplate

    # prompt case 1
    prompt = ChatPromptTemplate.from_template('{input}')

    # prompt case 2
    # prompt = ChatPromptTemplate.from_messages([
    #     ('system', 'You are a helpful assistant.'),
    #     ('user', '{input}')
    # ])

    parser = StrOutputParser()
    chain = prompt | llm | parser
    print(chain.invoke({'input': 'Who said "Hello, world!" for the first time?'}))
    print('-'*100)
    llm = LLMFactory(model='gpt-4o-2024-08-06', provider='azure_openai')
    chain = prompt | llm | parser
    print(chain.invoke({'input': 'Who said "Hello, world!" for the first time?'}))
    lllm=ChatOpenAI(
                model="deepseek-chat",
                temperature=0.0,
                api_key="",
                streaming=False,
                base_url="https://api.deepseek.com/v1",
            )   
    lllm.with_structured_output   