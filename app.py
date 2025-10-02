import time
import pandas as pd
import streamlit as st

from chat_engine import generate_behavior_tree, generate_behavior_tree_from_series, modify_behavior_tree

st.set_page_config(page_title="RobotBT", page_icon="🤖", layout="wide")

# ---------- State ----------
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "csv_df" not in st.session_state:
    st.session_state["csv_df"] = None

if "csv_selected_index" not in st.session_state:
    st.session_state["csv_selected_index"] = None

if "csv_selected_row" not in st.session_state:
    st.session_state["csv_selected_row"] = None

if "mode" not in st.session_state:
    st.session_state["mode"] = "Generate BT"

# ---------- BT State ----------
if "bt_state" not in st.session_state:
    st.session_state["bt_state"] = {
        "basic": {
            "last_xml": None,
            "processing_time": None,
            "versions": []
        },
        "csv": {
            "last_xml": None,
            "processing_time": None,
            "versions": []
        },
        "previous_mode": None  # 'basic' or 'csv'
    }


# ---------- Main: Chat UI (Chat + Modification auto-detect) ----------
st.markdown("## 🤖 RobotBT")

# ---------- CSV Upload & Row Selection ----------
with st.sidebar:
    # ---------- Upload CSV ----------
    st.markdown("### 📄 Upload CSV & Pick a Row")

    csv_file = st.file_uploader(
        "Upload CSV (use your template)",
        type=["csv"],
        key="csv_uploader_sidebar"
    )

    if csv_file is not None:
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            st.error(f"Failed to read CSV: {e}")
            df = None

        if df is not None:
            st.session_state["csv_df"] = df
            st.success(f"Loaded: {df.shape[0]} rows × {df.shape[1]} cols")

            name_col_exemplars = [c for c in df.columns if "name of the exemplar" in c.lower()]
            label_col = name_col_exemplars[0] if name_col_exemplars else None

            if label_col:
                choices = [f"[{i}] {str(df.iloc[i][label_col])}" for i in range(len(df))]
            else:
                choices = [f"[{i}] row {i}" for i in range(len(df))]

            if "csv_selected_index" not in st.session_state:
                st.session_state["csv_selected_index"] = 0 if len(choices) else None

            row_idx = st.selectbox(
                "Select a row",
                options=list(range(len(choices))),
                format_func=lambda i: choices[i],
                index=st.session_state["csv_selected_index"] if st.session_state[
                                                                    "csv_selected_index"] is not None else 0,
                key="csv_row_select_sidebar",
            )

            st.session_state["csv_selected_index"] = row_idx

            if row_idx is not None:
                st.dataframe(df.iloc[[row_idx]], width='stretch')

            gen_bt_with_all = st.button("🚀 Generate BT from CSV row", width='stretch', key="gen_bt_sidebar")
            if gen_bt_with_all and row_idx is not None:
                start_time = time.time()
                row = df.iloc[row_idx]
                with st.spinner("Generating behavior tree from CSV row..."):
                    try:
                        bt_xml = generate_behavior_tree_from_series(row)
                        end_time = time.time()
                        processing_time = end_time - start_time

                        st.session_state["bt_state"]["csv"]["processing_time"] = processing_time
                        st.session_state["bt_state"]["csv"]["last_xml"] = bt_xml
                        st.session_state["bt_state"]["csv"]["versions"].append((bt_xml, time.time(), processing_time))
                        st.session_state["bt_state"]["previous_mode"] = "csv"

                        st.session_state["messages"].append({
                            "role": "assistant",
                            "content": bt_xml + f"\n\n`⏱ Processing time: {processing_time:.2f} seconds`"
                        })
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # ---------- Mode buttons----------
    st.markdown("---")
    st.markdown(f"### 🧭 Current Mode: **{st.session_state['mode']}**")

    if "pending_mode" not in st.session_state:
        st.session_state["pending_mode"] = st.session_state["mode"]

    if st.button("Generate BT", key="mode_gen_sidebar", width='stretch'):
        st.session_state["pending_mode"] = "Generate BT"

    if st.button("Modification", key="mode_mod_sidebar", width='stretch'):
        st.session_state["pending_mode"] = "Modification"

    if st.button("ClearALL", key="mode_clear_sidebar", width='stretch'):
        st.session_state["pending_mode"] = "ClearALL"
        st.session_state["bt_state"] = {
            "basic": {"last_xml": None, "processing_time": None, "versions": []},
            "csv": {"last_xml": None, "processing_time": None, "versions": [], "last_csv_context": None,
                    "last_csv_row_id": None},
            "previous_mode": None
        }
        st.success("Memory and messages cleared.")
        st.session_state["messages"] = []
        st.rerun()

    if st.session_state["pending_mode"] != st.session_state["mode"]:
        st.session_state["mode"] = st.session_state["pending_mode"]
        st.rerun()

result_container = st.container()
with result_container:
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ---------- Chat input ----------
user_input = st.chat_input("Please enter your input...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state["messages"].append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⏳ Processing...")

        mode = st.session_state["mode"]

        try:
            print("mode is: ", mode)
            if mode == "Generate BT":
                # gen_bt(user_input)
                start_time = time.time()
                bt_xml = generate_behavior_tree(user_input)
                end_time = time.time()
                processing_time = end_time - start_time

                st.session_state["bt_state"]["basic"]["last_xml"] = bt_xml
                st.session_state["bt_state"]["basic"]["processing_time"] = processing_time
                st.session_state["bt_state"]["basic"]["versions"].append((bt_xml, time.time(), processing_time))
                st.session_state["bt_state"]["previous_mode"] = "basic"

                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": bt_xml + f"\n\n`⏱ Processing time: {processing_time:.2f} seconds`"
                })

            # elif mode == "Modification":
            else:
                xml_src = st.session_state["bt_state"]["previous_mode"] or "basic"
                base = st.session_state["bt_state"][xml_src]["last_xml"]

                if not base:
                    st.session_state["messages"].append(
                        {"role": "assistant", "content": "⚠️ Please generate a BT first before modifying."})
                else:
                    start_time = time.time()
                    modified_xml = modify_behavior_tree(base, user_input)
                    end_time = time.time()
                    processing_time = end_time - start_time

                    st.session_state["bt_state"][xml_src]["last_xml"] = modified_xml
                    st.session_state["bt_state"][xml_src]["processing_time"] = processing_time
                    st.session_state["bt_state"][xml_src]["versions"].append(
                        (modified_xml, time.time(), processing_time))

                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": modified_xml + f"\n\n`⏱ Processing time: {processing_time:.2f} seconds`"
                    })
        except Exception as e:
            placeholder.error(f"❌ Error: {e}")
            st.session_state["messages"].append({"role": "assistant", "content": f'❌ Error: {e}'})

    st.rerun()

else:
    st.empty()
