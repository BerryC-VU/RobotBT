# from langchain.chat_models import ChatOpenAI
# from langchain.memory import ConversationBufferMemory
# from langchain.chains import ConversationChain
# from dotenv import load_dotenv
# import os

# load_dotenv()

# def create_chat_engine():
#     api_key = os.getenv("OPENAI_API_KEY")
#     if not api_key:
#         raise ValueError("OPENAI_API_KEY not found in environment")

#     llm = ChatOpenAI(
#         temperature=0.3,
#         model_name="gpt-3.5-turbo",  
#         openai_api_key=api_key  
#     )

#     memory = ConversationBufferMemory(return_messages=True)
#     conversation = ConversationChain(llm=llm, memory=memory)
#     return conversation



import os
from dotenv import load_dotenv
from langchain_community.llms import Tongyi
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

load_dotenv()
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

def create_chat_engine():
    llm = Tongyi(
        dashscope_api_key=DASHSCOPE_API_KEY,
        model="qwen-max",  
        temperature=0.3
    )

    memory = ConversationBufferMemory(return_messages=True)
    return ConversationChain(llm=llm, memory=memory)

