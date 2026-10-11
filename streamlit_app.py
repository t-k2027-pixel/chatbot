import streamlit as st
import google.generativeai as genai

# Show title and description.
st.title("💬 Gemini Chatbot")
st.write(
    "This is a simple chatbot that uses Google's Gemini model to generate responses. "
    "To use this app, you need to provide a Gemini API key, which you can get [here](https://aistudio.google.com/app/apikey). "
)

# Ask user for their Gemini API key via `st.text_input`.
gemini_api_key = st.text_input("Gemini API Key", type="password")
if not gemini_api_key:
    st.info("Please add your Gemini API key to continue.", icon="🗝️")
else:
    # Configure the Gemini API client
    genai.configure(api_key=gemini_api_key)
    
    # Initialize the Gemini model (gemini-1.5-flash is fast and recommended for general chat)
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Create a session state variable to store the chat messages.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message.
    if prompt := st.chat_input("What is up?"):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 過去のメッセージ履歴をGemini APIの形式に変換
        # Streamlitの "assistant" ロールを Geminiの "model" ロールにマッピングします
        gemini_history = []
        for msg in st.session_state.messages[:-1]:  # 最新のプロンプトを除く
            role = "model" if msg["role"] == "assistant" else "user"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

        # チャットセッションの開始（履歴を引き継ぐ）
        chat = model.start_chat(history=gemini_history)

        # 応答の生成（ストリーミングを有効化）
        response = chat.send_message(prompt, stream=True)

        # Streamlitの st.write_stream 用に、テキストチャンクを返すジェネレーターを定義
        def stream_generator():
            for chunk in response:
                if chunk.text:
                    yield chunk.text

        # Stream the response to the chat using `st.write_stream`
        with st.chat_message("assistant"):
            full_response = st.write_stream(stream_generator())
            
        # 最終的な応答をセッションステートに保存
        st.session_state.messages.append({"role": "assistant", "content": full_response})
