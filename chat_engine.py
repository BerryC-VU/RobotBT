import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatTongyi


load_dotenv()
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")


# LLM
llm = ChatTongyi(model="qwen-max")

gen_bt_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a robotics behavior tree expert.
Please extract the key behavior tree nodes (actions, conditions, sequences, selectors, decorators, etc.)
from the following scenario description. Then, format and return ONLY the entire behavior tree
into a proper BTCPP_format 4 BT XML format. Do NOT include explanations or structured lists.
Return ONLY the XML inside."""),
    ("user", "{description}")
])


mod_bt_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a robotics behavior tree expert.
The user will give you an existing BT (in XML) and a modification request.
You must update the XML accordingly and return ONLY the full modified BT in BTCPP_format 4 XML.
Do NOT include explanations or comments. Output only valid XML."""),
    ("user", "Existing BT:\n{last_xml}\n\nModification request:\n{instruction}")
])


chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant for general conversation."),
    ("user", "{message}")
])


def generate_behavior_tree(description: str) -> str:
    chain = gen_bt_prompt | llm
    response = chain.invoke({"description": description})
    if isinstance(response, dict) and "content" in response:
        return response["content"]
    if hasattr(response, "content"):
        return response.content
    return str(response)


def modify_behavior_tree(last_xml: str, instruction: str) -> str:
    chain = mod_bt_prompt | llm
    response = chain.invoke({"last_xml": last_xml, "instruction": instruction})
    if isinstance(response, dict) and "content" in response:
        return response["content"]
    if hasattr(response, "content"):
        return response.content
    return str(response)


def chat_reply(message: str) -> str:
    chain = chat_prompt | llm
    response = chain.invoke({"message": message})
    if isinstance(response, dict) and "content" in response:
        return response["content"]
    if hasattr(response, "content"):
        return response.content
    return str(response)
