import streamlit as st
import google.generativeai as genai
from datetime import datetime, timezone, timedelta
import urllib.request
import json  # 【追加】天気データを処理するためのライブラリ

# 上司のメールアドレス（ダミー）
BOSS_EMAIL = "boss_taro@example.co.jp"

# タイトルと説明文
st.title("☀️ 朝の健康・タスク確認アシスタント")
st.write(
    "1日の始まりに、今日の体調とタスクをAIと確認しましょう！ "
    "回答に応じてAIが質問を変え、最後に今日の情報をまとめてくれます。"
)

# APIキーの取得
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("APIキーが設定されていません。Streamlit Cloudの「Secrets」設定を確認してください。")
    st.stop()

# APIキーの設定
genai.configure(api_key=gemini_api_key)

# 日本時間の取得
JST = timezone(timedelta(hours=+9), 'JST')
today_str = datetime.now(JST).strftime("%Y年%m月%d日")

# 【修正】大阪の天気を取得する（Open-Meteo APIを使用）
try:
    # 大阪の緯度・経度を指定して、現在の天気と最高・最低気温を取得
    url = "https://api.open-meteo.com/v1/forecast?latitude=34.6937&longitude=135.5022&daily=temperature_2m_max,temperature_2m_min&current_weather=true&timezone=Asia%2FTokyo"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=3) as response:
        data = json.loads(response.read().decode('utf-8'))
        
        # 天気コードを絵文字に変換
        wmo_codes = {
            0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️',
            45: '🌫️', 48: '🌫️', 51: '🌧️', 53: '🌧️', 55: '🌧️',
            61: '☔', 63: '☔', 65: '☔', 71: '⛄', 73: '⛄', 75: '⛄',
            95: '⚡', 96: '⛈️', 99: '⛈️'
        }
        code = data['current_weather']['weathercode']
        icon = wmo_codes.get(code, '☁️') # 当てはまらない場合はデフォルトで曇り
        
        # 必要な数値を抽出して文章を組み立てる
        current_temp = data['current_weather']['temperature']
        max_temp = data['daily']['temperature_2m_max'][0]
        min_temp = data['daily']['temperature_2m_min'][0]
        
        # ご要望の形式にフォーマット
        osaka_weather = f"{icon} 現在 {current_temp}℃ (最高 {max_temp}℃ / 最低 {min_temp}℃)"
except Exception:
    osaka_weather = "取得できませんでした（晴れるといいですね！）"

# アラート機能の指示をシステムプロンプトに追加
system_instruction = f"""
あなたは企業の親切な「朝の健康・タスク管理アシスタント」です。
今日の日付は{today_str}、現在の大阪の天気予報は「{osaka_weather}」です。

あなたの目的は、社員と自然な会話をしながら以下の項目を順番にヒアリングし、最後にまとめることです。

【ヒアリングのステップ】
ステップ1: 健康状態の確認
・今日の体調
・昨日のアルコール摂取の有無
・よく眠れたか（睡眠の質）

ステップ2: 健康状態の深掘り
ステップ1の回答で「体調がよくない」「アルコールを摂取した」「よく眠れなかった」のいずれかに該当する場合は、タスクの話に進む前に必ず詳細（理由や現在の辛さなど）を優しく尋ねてください。

ステップ3: タスクの確認
健康状態の確認が終わったら、「今日のタスク内容」について聞いてください。

ステップ4: 締めくくり
タスク内容を聞き終わったら、以下の構成で出力して会話を終了してください。
1. 本日のヒアリング内容のまとめ（綺麗な箇条書きで）
2. 今日の大阪の天気（「{osaka_weather}」を含める）
3. 社員が1日を頑張れるような、前向きで「元気になるひとこと」

【重要：上司への自動報告アラート】
社員の回答から「体調不良（発熱など）」「アルコール摂取（二日酔いや飲酒の事実）」「極端な睡眠不足」のいずれかが認められた場合、あなたの**返答テキストの一番最後に必ず `[ALERT]` という文字列を含めて**ください。システムがこれを検知して上司に連絡します。（※ユーザーを責めるのではなく、心配するトーンを保ってください）

【会話のルール】
- 相手の回答には、常に労いや共感の言葉をかけてください。
- 一度にたくさん質問せず、会話のキャッチボールを意識してください。
"""

model = genai.GenerativeModel(
    "models/gemini-3.8-flash",
    system_instruction=system_instruction
)

# セッションステートの初期化
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "おはようございます！今日も1日よろしくお願いします。\nまずは、**今日の体調**、**昨晩のアルコール摂取の有無**、そして**よく眠れたかどうか**を教えてください。"}
    ]

# メッセージ履歴の表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザーからの入力
if prompt := st.chat_input("ここに入力（例：少し寝不足ですが、アルコールは飲んでいません）"):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    gemini_history = []
    for msg in st.session_state.messages[:-1]:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    try:
        chat = model.start_chat(history=gemini_history)

        with st.spinner("AIが入力内容を確認中..."):
            response = chat.send_message(prompt, stream=False)
            
            # AIの返答からアラートのタグを検知する
            reply_text = response.text
            alert_triggered = False
            
            if "[ALERT]" in reply_text:
                alert_triggered = True
                # ユーザーの画面には [ALERT] という文字を見せないように削除する
                reply_text = reply_text.replace("[ALERT]", "").strip()

        # AIの回答を表示
        with st.chat_message("assistant"):
            st.markdown(reply_text)
            
        # アラートが検知された場合、警告メッセージを表示
        if alert_triggered:
            st.error(f"⚠️ 【システム通知】体調不良または睡眠不足・アルコール摂取が検知されました。\n安全のため、上司（{BOSS_EMAIL}）へ自動的に報告メールを送信しました。無理をせず、必要があればお休みを取ってください。")
            
        st.session_state.messages.append({"role": "assistant", "content": reply_text})

    except Exception as e:
        st.error(f"APIエラーが発生しました。詳細: {str(e)}")
