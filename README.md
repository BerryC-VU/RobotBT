# 🤖 RobotBT

A simple interactive Behavior Tree extractor powered by LangChain(DashScope) and Streamlit.



## 🚀 Getting Started

Follow the steps below to set up and run the project locally.

### 1. Clone the Repository

```bash
git clone https://github.com/BerryC-VU/RobotBT.git
cd RobotBT
```

### 2. Install Dependencies

Make sure you have Python 3.10+ installed.

Install all required packages:

```bash
pip install -r requirements.txt
```

### 3. Set up Environment Variables

Create a `.env` file in the project root directory, and add your [DashScope API Key](https://dashscope.console.aliyun.com/apiKey):

```env
DASHSCOPE_API_KEY=your_api_key_here
```

> 🔒 **Do not share your API key publicly.**

### 4. Run the App

Launch the Streamlit app:

```bash
streamlit run app.py
```

---

## 📦 Features

- Extracts Behavior Tree structures from scenario descriptions
- Powered by DashScope LLM
- Streamlit-based UI for interactive usage

---

