
import os
import random
from typing import Literal, Optional
from langchain_openai import AzureChatOpenAI, ChatOpenAI

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
        provider: Literal['azure_openai', 'openai'] = 'azure_openai',
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
                api_key=api_key or os.environ['BIGAI_OAI_API_KEY'],
                api_version=api_version or os.environ['BIGAI_API_VERSION'],
                azure_endpoint=azure_endpoint or f"{os.environ['BIGAI_API_BASE']}/{region}",
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
        else:
            raise ValueError(f"Unsupported provider: {provider}")

