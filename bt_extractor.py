def extract_bt_from_description(chat_engine, description: str):
    prompt = f"""
        You are a robotics behavior tree expert. Please extract the key behavior tree nodes 
        (actions, conditions, sequences, selectors, decorators, etc.) from the following scenario description, 
        Then, format and return ONLY the entire behavior tree into a proper BTCPP_format 4 BT XML format. 
        Do NOT include explanations or structured lists.
        Return ONLY the XML inside.
        
        The description is:
        \"\"\"
        {description}
        \"\"\"
    """

    
    output = chat_engine.invoke(prompt)
    return output["response"]

