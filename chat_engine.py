import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatTongyi
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

load_dotenv()
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")


store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


# LLM
llm = ChatTongyi(model="qwen-max")

# prompts
gen_bt_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a robotics behavior tree expert.
Please extract the key behavior tree nodes (actions, conditions, sequences, selectors, decorators, etc.)
from the following scenario description. Then, format and return ONLY the entire behavior tree
into a proper BTCPP_format 4 BT XML format. Do NOT include explanations or structured lists.
Return ONLY the XML inside."""),
    ("placeholder", "{history}"),
    ("user", "{description}")
])


mod_bt_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a robotics behavior tree expert.
The user will give you an existing BT (in XML) and a modification request.
You must update the XML accordingly and return ONLY the full modified BT in BTCPP_format 4 XML.
Do NOT include explanations or comments. Output only valid XML."""),
    ("placeholder", "{history}"),
    ("user", "Existing BT:\n{last_xml}\n\nModification request:\n{instruction}")
])


chat_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant for general conversation. 
Keep your answers short, concise, and directly relevant to the user's request. 
Do not provide long explanations unless explicitly asked."""),
    ("placeholder", "{history}"),
    ("user", "{message}")
])


def generate_behavior_tree(description: str, session_id: str = "default") -> str:
    chain_with_history = RunnableWithMessageHistory(
        gen_bt_prompt | llm,
        get_session_history,
        input_messages_key="description",
        history_messages_key="history",
    )
    response = chain_with_history.invoke(
        {"description": description},
        config={"configurable": {"session_id": session_id}}
    )
    if isinstance(response, dict) and "content" in response:
        return response["content"]
    if hasattr(response, "content"):
        return response.content
    return str(response)


def modify_behavior_tree(last_xml: str, instruction: str, session_id: str = "default") -> str:
    chain_with_history = RunnableWithMessageHistory(
        mod_bt_prompt | llm,
        get_session_history,
        input_messages_key="instruction",
        history_messages_key="history",
    )
    response = chain_with_history.invoke(
        {"last_xml": last_xml, "instruction": instruction},
        config={"configurable": {"session_id": session_id}}
    )
    if isinstance(response, dict) and "content" in response:
        return response["content"]
    if hasattr(response, "content"):
        return response.content
    return str(response)


def chat_reply(message: str, session_id: str = "default") -> str:
    chain_with_history = RunnableWithMessageHistory(
        chat_prompt | llm,
        get_session_history,
        input_messages_key="message",
        history_messages_key="history",
    )
    response = chain_with_history.invoke(
        {"message": message},
        config={"configurable": {"session_id": session_id}}
    )
    if isinstance(response, dict) and "content" in response:
        return response["content"]
    if hasattr(response, "content"):
        return response.content
    return str(response)
