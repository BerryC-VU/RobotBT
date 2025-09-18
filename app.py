import streamlit as st
from chat_engine import generate_behavior_tree, modify_behavior_tree, chat_reply
import time
from chat_engine import store

st.markdown("## 🧠 Behavior Tree Extractor ChatBot")

if "session_id" not in st.session_state:
    st.session_state["session_id"] = "default"


if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "last_xml" not in st.session_state:
    st.session_state["last_xml"] = ""
if "mode" not in st.session_state:
    st.session_state["mode"] = "Chat"

GEN_KWS = ["generate bt", "generate behavior tree", "extract bt", "extract behavior tree"]
MOD_KWS = ["modify", "update", "edit", "change", "delete"]


def detect_mode(s: str) -> str:
    s_low = s.lower()
    if any(k in s_low for k in GEN_KWS):
        return "generate"
    if any(k in s_low for k in MOD_KWS):
        return "modify"
    return "chat"


for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Please enter your input...")

if "mode" not in st.session_state:
    st.session_state["mode"] = "Chat"
if "pending_mode" not in st.session_state:
    st.session_state["pending_mode"] = st.session_state["mode"]

col1, col2, col3, col4, col5 = st.columns([3, 1.75, 1.75, 1, 1.5])
with col1:
    st.write(f"👉 Current mode: **{st.session_state['mode']}**")
with col2:
    if st.button("Generate BT"):
        st.session_state["pending_mode"] = "Generate BT"
with col3:
    if st.button("Modification"):
        st.session_state["pending_mode"] = "Modification"
with col4:
    if st.button("Chat"):
        st.session_state["pending_mode"] = "Chat"
with col5:
    if st.button("ClearALL"):
        st.session_state["pending_mode"] = "ClearALL"
        if st.session_state["session_id"] in store:
            store.pop(st.session_state["session_id"])
        st.session_state["messages"] = []
        st.session_state["last_xml"] = ""
        st.session_state["pending_mode"] = "Chat"
        st.success("Memory and messages cleared.")
        st.rerun()

if st.session_state["pending_mode"] != st.session_state["mode"]:
    st.session_state["mode"] = st.session_state["pending_mode"]
    st.rerun()

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state["messages"].append({"role": "user", "content": user_input})
    start_time = time.time()

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⏳ Processing...")

        if st.session_state["mode"] == "Chat":
            mode = detect_mode(user_input)
        else:
            mode = st.session_state["mode"]

        try:
            print("mode is: ", mode)
            if mode == "Generate BT":
                bt_xml = generate_behavior_tree(user_input,
                                                session_id=st.session_state["session_id"]
                                                )
                end_time = time.time()
                processing_time = end_time - start_time

                st.session_state["last_xml"] = bt_xml
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": bt_xml + f"\n\n`⏱ Processing time: {processing_time:.2f} seconds`"
                })

            elif mode == "Modification":
                if st.session_state["last_xml"]:
                    modified_xml = modify_behavior_tree(st.session_state["last_xml"],
                                                        user_input,
                                                        session_id=st.session_state["session_id"]
                                                        )
                    end_time = time.time()
                    processing_time = end_time - start_time

                    st.session_state["last_xml"] = modified_xml
                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": modified_xml + f"\n\n`⏱ Processing time: {processing_time:.2f} seconds`"
                    })
                else:
                    st.session_state["messages"].append(
                        {"role": "assistant", "content": "⚠️ Please generate a BT first before modifying."})

            else:
                reply = chat_reply(user_input, session_id=st.session_state["session_id"])
                st.session_state["messages"].append({"role": "assistant", "content": reply})

        except Exception as e:
            placeholder.error(f"❌ Error: {e}")
            st.session_state["messages"].append({"role": "assistant", "content": f'❌ Error: {e}'})

    st.rerun()

else:
    st.empty()
