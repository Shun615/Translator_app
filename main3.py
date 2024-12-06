import os
import asyncio
import streamlit as st
import speech_recognition as sr
import deepl
import edge_tts
from dotenv import load_dotenv

# API.envファイルから環境変数を読み込む
load_dotenv("API.env")

# セッション状態の初期化
# ① 初期化：セッション状態が空である場合、初期化（空文字列を設定）。これにより、後続の処理でキーエラーを回避
# ② 状態の更新:音声認識機能を実行すると、st.session_state["input_text"] が更新。
# ③ 状態の再利用:ユーザーが別のボタンを押したり、ページを再レンダリングしても、st.session_state に保存された値は保持。
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""
if "translated_text" not in st.session_state:
    st.session_state["translated_text"] = ""

# DeepL翻訳関数
def deepl_translate(text, target_lang="EN-US"):
    API_KEY = os.getenv("DEEPL_API_KEY")  # 環境変数からDeepL APIキーを取得
    if not API_KEY:
        st.error("DeepL APIキーが設定されていません。環境変数にDEEPL_API_KEYを設定してください。")
        return "翻訳エラー: APIキーが見つかりません。"

    try:
        translator = deepl.Translator(API_KEY)
        result = translator.translate_text(text, target_lang=target_lang)
        return result.text
    except Exception as e:
        st.error(f"翻訳中にエラーが発生しました: {str(e)}")
        return "翻訳エラー"

# 音声認識関数
def recognize_speech():
    r = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        st.info("Recording... Please speak into the microphone.")
        audio = r.listen(source)
        st.success("Recording complete!")
        try:
            return r.recognize_google(audio, language="ja-JP")
        except sr.UnknownValueError:
            return "音声を認識できませんでした。"
        except sr.RequestError:
            return "音声認識サービスに接続できませんでした。"

# Edge TTS音声合成関数
async def text_to_speech(text, voice, output_file="output.mp3", rate="0%", pitch="0Hz"):
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(output_file)
    except Exception as e:
        st.error(f"音声生成中にエラーが発生しました: {str(e)}")

# Streamlitアプリケーション
st.title("音声翻訳＆音声化アプリ")

# 音声録音ボタン
if st.button("Record Speech"):
    st.session_state["input_text"] = recognize_speech()

# テキストエリア
input_text = st.text_area("認識されたテキスト", st.session_state["input_text"], height=200)

# 翻訳セクション
st.subheader("翻訳機能")

LANGUAGES = {
    "英語（アメリカ）": "EN-US",
    "英語（イギリス）": "EN-GB",
    "日本語": "JA",
    "中国語": "ZH",
}
target_lang = st.selectbox("翻訳先言語を選択してください", options=list(LANGUAGES.keys()))

if st.button("Translate"):
    st.session_state["translated_text"] = deepl_translate(input_text, target_lang=LANGUAGES[target_lang])

# 翻訳結果を表示
st.text_area("翻訳結果", st.session_state["translated_text"], height=200)

# 音声化セクション
st.subheader("翻訳結果を音声化")

# 声質の選択
voice = st.selectbox(
    'Voice', 
    ['ja-JP-KeitaNeural', 'ja-JP-NanamiNeural', 'en-US-JessaNeural', 
     'zh-CN-XiaoxiaoNeural', 'zh-CN-YunyangNeural', 'ko-KR-SunHiNeural']
)

# 音声速度の調整
rate = st.slider('Rate', -100, 100, 20)

# 音声ピッチの調整
pitch = st.slider('Pitch', -100, 100, 0)

# 音声生成ボタン
if st.button("Generate Speech"):
    if st.session_state["translated_text"]:
        output_file = "translated_speech.mp3"
        rate_str = f"{rate:+}%"
        pitch_str = f"{pitch:+}Hz"
        asyncio.run(text_to_speech(st.session_state["translated_text"], voice, output_file, rate=rate_str, pitch=pitch_str))
        st.audio(output_file)
    else:
        st.warning("翻訳結果がありません。まず翻訳を行ってください。")

# 音声ファイルの削除
if os.path.exists("translated_speech.mp3") and st.button("Delete Audio"):
    os.remove("translated_speech.mp3")
    st.info("Audio file deleted.")
