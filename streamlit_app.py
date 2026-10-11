import streamlit as st
import google.generativeai as genai
from datetime import datetime, timezone, timedelta

# タイトルと説明文
st.title("📋 健康管理・業務報告アシスタント")
st.write(
    "1日の終わりに、AIとチャットしながら今日の体調と業務報告を行いましょう。 "
    "AIからの質問に答えていくと、最後に日報としてまとめてくれます。"
)

# APIキーの取得（st.secretsから）
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("APIキーが設定されていません。Streamlit Cloudの「Secrets」設定を確認してください。")
    st.stop()

# APIキーの設定（ここから下はすべて左端に揃えます）
genai.configure(api_key=gemini_api_key)

# 日本時間の取得
JST = timezone(timedelta(hours=+9), 'JST')
today_str = datetime.now(JST).strftime("%Y年%m月%d日")

# AIの役割（システムプロンプト）
system_instruction = f"""
あなたは企業の親切な「健康管理・業務報告アシスタント」です。
今日の日付は{today_str}です。

あなたの目的は、社員と自然な会話をしながら以下の4つの項目を引き出すことです。
1. 今日の体調（気分、睡眠不足がないかなど）
2. 本日の主な業務内容・成果
3. 業務上で困っていることや課題
4. 明日の主な予定

【ルール】
- 一度にすべての項目を質問するのではなく、会話のキャッチボールを通じて1つ〜2つずつ優しく聞いてください。
- 社員の回答に対しては、まず労いや共感の言葉（「お疲れ様です」「それは大変でしたね」「素晴らしいですね」など）をかけてください。
- 4つの項目すべてを聞き終わったら、「本日の日報まとめ」として綺麗な箇条書きのフォーマットで出力し、「今日もお疲れ様でした！ゆっくり休んでくださいね。」と締めくくってください。
"""

# モデルの初期化
model = genai.GenerativeModel(
    "models/gemini-3.8-flash",
    system_instruction=system_instruction
)

# セッションステートの初期化
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "今日もお疲れ様です！まずは本日の体調はいかがですか？（よく眠れたか、疲れはないか等教えてください）"}
    ]

# メッセージ履歴の表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザーからの入力
if prompt := st.chat_input("ここに入力（例：少し寝不足ですが、体調は問題ないです）"):
    
    # ユーザーのメッセージを表示して保存
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 履歴をAPI形式に変換
    gemini_history = []
    for msg in st.session_state.messages[:-1]:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    try:
        chat = model.start_chat(history=gemini_history)

        # 考え中アニメーションを表示しつつ一括でレスポンスを取得
        with st.spinner("AIが入力内容を確認中..."):
            response = chat.send_message(prompt, stream=False)

        # AIの回答を表示して保存
        with st.chat_message("assistant"):
            st.markdown(response.text)
            
        st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"APIエラーが発生しました。詳細: {str(e)}")
