import streamlit as st
import google.generativeai as genai
from datetime import datetime, timezone, timedelta

# Show title and description.
st.title("💬 Gemini Chatbot")
st.write(
    "This is a simple chatbot that uses Google's Gemini model to generate responses. "
    "To use this app, you need to provide a Gemini API key."
)

# Ask user for their Gemini API key
gemini_api_key =st.secrets['app.py_APIKey']
if not gemini_api_key:
    st.info("Please add your Gemini API key to continue.", icon="🗝️")
else:
    # Configure the Gemini API client
    genai.configure(api_key=gemini_api_key)
    
    # 【修正1】Streamlit Cloudは海外サーバーなので、日本時間（JST）を取得する設定を追加
    JST = timezone(timedelta(hours=+9), 'JST')
    today_str = datetime.now(JST).strftime("%Y年%m月%d日")

    # 【修正2】system_instructionを使って、AIに今日の日付と役割を教え込む
    model = genai.GenerativeModel(
        "models/gemini-3.8-flash",
        system_instruction=f"あなたは親切なAIアシスタントです。今日の日付は{today_str}です。"
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        gemini_history = []
        for msg in st.session_state.messages[:-1]:
            role = "model" if msg["role"] == "assistant" else "user"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

        try:
            chat = model.start_chat(history=gemini_history)

            # 【修正3】stream=False に変更。少し待機したのち、回答が一瞬で表示されるようになります
            with st.spinner("AIが考え中..."):
                response = chat.send_message(prompt, stream=False)

            with st.chat_message("assistant"):
                st.markdown(response.text)
                
            st.session_state.messages.append({"role": "assistant", "content": response.text})

        except Exception as e:
            st.error(f"APIエラーが発生しました。詳細: {str(e)}")
