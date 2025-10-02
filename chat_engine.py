import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatTongyi
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

import pandas as pd

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


def parse_series_to_requirements(row_data):
    try:
        requirements = {
            "mission_description": "",
            "technical_capabilities": [],
            "operational_capabilities": [],
            "uncertainties": [],
            "adaptation_goals": []
        }

        # Mission description
        description_col = "Description (the textual description of the robotic mission)"
        requirements["mission_description"] = row_data[description_col]
        # if description_col in row_data.index and pd.notna(row_data[description_col]):
        #     requirements["mission_description"] = row_data[description_col]

        # Technical capabilities
        tech_cols = ["Robot Features", "Technical Capabilities"]
        for col in tech_cols:
            if col in row_data.index and pd.notna(row_data[col]):
                requirements["technical_capabilities"].append(row_data[col])

        # Operational capabilities
        op_cols = "Operational Capabilities"
        requirements["operational_capabilities"] = row_data[op_cols]

        # Uncertainties
        uncertainty_cols = [
            "Model Drift", "Sensing", "Mission Specification",
            "Human in the Loop", "Execution Context", "Abstraction",
            "Incompleteness", "Different Sources of information",
            "Complex Models", "Variability Space", "Automatic learning",
            "Decentralization & Coordination", "Future Mission Changes",
            "OutdatedMission", "New or defunct capabilities", "Changing capabilities",
            "Actuation"
        ]

        for col in row_data.index:
            for keyword in uncertainty_cols:
                if keyword in col.lower():
                    val = row_data[col]
                    if pd.notna(val):
                        requirements["uncertainties"].append(f"{keyword}: {row_data[col]}")

        # Adaptation goals
        adaptation_cols = [
            "Types  of  adaptation (self* properties)",
            "Adaptation concerns, constraints and other factors"
        ]
        for col in adaptation_cols:
            if col in row_data.index and pd.notna(row_data[col]):
                requirements["adaptation_goals"].append(row_data[col])

        return requirements

    except Exception as e:
        return {"error": f"Error parsing Series: {str(e)}"}


def format_requirements_prompt(requirements):
    if "error" in requirements:
        return requirements["error"]

    prompt_parts = []

    # Mission description
    if requirements["mission_description"]:
        prompt_parts.append(f"MISSION DESCRIPTION:\n{requirements['mission_description']}")

    # Technical capabilities
    if requirements["technical_capabilities"]:
        prompt_parts.append("\nTECHNICAL CAPABILITIES:")
        for capability in requirements["technical_capabilities"]:
            if capability:  # Check if not empty
                prompt_parts.append(f"- {capability}")

    # Operational capabilities
    if requirements["operational_capabilities"]:
        prompt_parts.append(f"\nOPERATIONAL CAPABILITIES:\n{requirements['operational_capabilities']}")

    # Uncertainties
    if requirements["uncertainties"]:
        prompt_parts.append("\nUNCERTAINTIES AND CHALLENGES:")
        for uncertainty in requirements["uncertainties"]:
            if uncertainty and not uncertainty.endswith(": nan"):  # Filter out NaN values
                prompt_parts.append(f"- {uncertainty}")

    # Adaptation goals
    if requirements["adaptation_goals"]:
        prompt_parts.append("\nADAPTATION GOALS:")
        for goal in requirements["adaptation_goals"]:
            if goal:  # Check if not empty
                prompt_parts.append(f"- {goal}")

    prompt_parts.append("""
ROBUSTNESS REQUIREMENTS:
- For sensing actions (scanning, detection): Add retry mechanisms (3 attempts) and fallback to manual operation
- For authorization actions: Add timeout handling and escalation procedures  
- For time-critical operations: Add compliance checking and violation recording
- For physical operations: Add retry logic and manual mode fallback
- For security-sensitive operations: Add secure logging and validation checks
- Handle human unpredictability with notification and waiting mechanisms
- Address model drift and sensor uncertainties with redundant verification
- Use Fallback nodes for error recovery and Selector nodes for alternative strategies
""")

    return "\n".join(prompt_parts)

series_bt_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a robotics behavior tree expert specializing in creating robust, adaptive systems.

Based on the comprehensive requirements provided, generate a behavior tree that:

1. Implements the core mission functionality from the mission description
2. Incorporates all specified technical and operational capabilities
3. Addresses all mentioned uncertainties and challenges with appropriate fallback mechanisms
4. Achieves the specified adaptation goals through self-management and self-organization properties
5. Includes robust error handling for all potential failure points

KEY ROBUSTNESS PATTERNS TO APPLY:
- Sensing/Perception failures: Retry 3x → Notify operator → Manual input
- Authorization failures: Check authorization → Wait for authorization → Escalate to supervisor
- Time compliance: Track time → Check compliance → Record violations
- Physical operation failures: Retry → Switch to manual mode → Notify operator
- Security operations: Validate security context → Secure action → Secure logging
- Human interaction: Notify human → Wait for response → Handle timeout

Return ONLY the complete behavior tree in BTCPP_format 4 XML format.
Do NOT include explanations or comments."""),
    ("placeholder", "{history}"),
    ("user", "{requirements}")
])


def generate_behavior_tree_from_series(row: "pd.Series", session_id: str = "default") -> str:
    requirements = parse_series_to_requirements(row)
    if "error" in requirements:
        return f"Error: {requirements['error']}"

    requirements_text = format_requirements_prompt(requirements)

    chain_with_history = RunnableWithMessageHistory(
        series_bt_prompt | llm,
        get_session_history,
        input_messages_key="requirements",
        history_messages_key="history",
    )

    response = chain_with_history.invoke(
        {"requirements": requirements_text},
        config={"configurable": {"session_id": session_id}}
    )

    # print("\n\nTHIS IS THE RESPONSE: ", response)

    if isinstance(response, dict) and "content" in response:
        return response["content"]
    if hasattr(response, "content"):
        return response.content
    return str(response)


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
