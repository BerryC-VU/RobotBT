import time
import pandas as pd
import streamlit as st

from chat_engine_a import generate_behavior_tree, generate_behavior_tree_from_series, modify_behavior_tree, chat_reply
from chat_engine_a import store


st.set_page_config(page_title="RobotBT", page_icon="🤖", layout="wide")

# ---------- State ----------
if "session_id" not in st.session_state:
    st.session_state["session_id"] = "default"

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "last_bt_xml" not in st.session_state:
    st.session_state["last_bt_xml"] = None

if "last_pt" not in st.session_state:
    st.session_state["last_pt"] = 0.0

if "csv_df" not in st.session_state:
    st.session_state["csv_df"] = None

if "csv_selected_index" not in st.session_state:
    st.session_state["csv_selected_index"] = None

if "csv_selected_row" not in st.session_state:
    st.session_state["csv_selected_row"] = None

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


st.markdown("## 🤖 RobotBT")


# ---------- CSV Upload & Row Selection ----------
with st.expander("📄 Upload CSV & Generate from a row", expanded=True):
    csv_file = st.file_uploader("Upload CSV (use your template)", type=["csv"], key="csv_uploader_single")

    if csv_file is not None:
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            st.error(f"Failed to read CSV: {e}")

        st.session_state["csv_df"] = df
        st.success(f"Loaded CSV file: {df.shape[0]} rows, {df.shape[1]} columns")

        if len(df) > 0:
            name_col_exemplars = [c for c in df.columns if "name of the exemplar" in c.lower()]
            label_col = name_col_exemplars[0] if name_col_exemplars else None

            if label_col:
                choices = [f"[{i}] {str(df.iloc[i][label_col])}" for i in range(len(df))]
            else:
                choices = [f"[{i}] row {i}" for i in range(len(df))]

            row_idx = st.selectbox("Select a row", options=list(range(len(choices))),
                                   format_func=lambda i: choices[i]) if len(choices) else None

            if row_idx is not None:
                st.dataframe(df.iloc[[row_idx]])

            gen_bt_with_all = st.button("🚀 Generate BT from CSV row")
            if gen_bt_with_all and row_idx is not None:
                start_time = time.time()
                row = df.iloc[row_idx]
                with st.spinner("Generating behavior tree from CSV row..."):
                    try:
                        bt_xml = generate_behavior_tree_from_series(row, session_id=st.session_state["session_id"])
                        end_time = time.time()
                        processing_time = end_time - start_time
                        st.session_state["last_pt"] = processing_time
                        st.session_state["last_xml"] = bt_xml
                        st.session_state["messages"].append({
                            "role": "assistant",
                            "content": bt_xml + f"\n\n`⏱ Processing time: {processing_time:.2f} seconds`"
                        })
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

result_container = st.container()
with result_container:
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


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

# Chat input
user_input = st.chat_input("Please enter your input...")

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
