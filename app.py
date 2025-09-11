import streamlit as st
from chat_engine import create_chat_engine
from bt_extractor import extract_bt_from_description
import re

def extract_bt_xml(text: str):
    """从模型回复中提取 <root>...</root> 的 XML 内容"""
    match = re.search(r"<root>.*?</root>", text, re.DOTALL)
    return match.group(0) if match else text

st.set_page_config(page_title="Behavior Tree ChatBot", layout="centered", page_icon="🤖")

st.title("🧠 Behavior Tree Extractor ChatBot")
st.markdown("Please enter your robot mission description, I'll extract the key components into an XML formated behavior tree.")


if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = create_chat_engine()


user_input = st.chat_input("Please enter your input...")

if user_input:
    with st.spinner("Generating Behavior Tree..."):
        try:
            response = extract_bt_from_description(
                st.session_state.chat_engine,
                user_input
            )
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                # st.code(response, language="xml")
                clean_result = extract_bt_xml(response)
                print("This is the cleaned result; \n")
                print(clean_result)
                clean_result = clean_result.replace("\\n", "\n")
                st.code(clean_result, language="xml")

        except Exception as e:
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                st.error(f"❌ Error：{e}")
