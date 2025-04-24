import streamlit as st
import pandas as pd
from datetime import datetime
from langchain_openai import ChatOpenAI

st.set_page_config(page_title="Questo - Creativity Assistant", layout="centered")

if 'page' not in st.session_state:
    st.session_state.page = 1
if 'user_id' not in st.session_state:
    st.session_state.user_id = f"User_{datetime.now().strftime('%H%M%S')}"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'chatgpt_history' not in st.session_state:
    st.session_state.chatgpt_history = []
if 'language' not in st.session_state:
    st.session_state.language = None
if 'llm' not in st.session_state:
    st.session_state.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

def next_page():
    st.session_state.page += 1

def prev_page():
    st.session_state.page -= 1

# 自動語言選擇 + 跳轉
if st.session_state.page == 1:
    st.title("🏁 活動挑戰說明")
    st.session_state.language = st.selectbox("Choose your language / 選擇語言", ["English", "中文"], index=0, key="lang_auto_select")
    st.session_state.page = 2
    st.rerun()

# 防止語言選完但仍停留在第一頁造成重疊
if st.session_state.page == 1:
    st.stop()

# 顯示語言在每頁頂部
if st.session_state.language:
    st.markdown(f"🌐 **Current Language**: `{st.session_state.language}`")

lang_code = 'E' if st.session_state.language == 'English' else 'C'

# 第 2 頁：初步構想
if st.session_state.page == 2:
    st.title("💡 初步構想發想")
    activity = st.text_area("請輸入三個最具創意的想法 / Your 3 ideas", key="activity_input")
    if activity:
        st.session_state.activity = activity
    if st.button("下一頁 / Next", key="next_page2"):
        next_page()

# 第 3 頁：與小Q聊天（內建氣泡）
elif st.session_state.page == 3:
    st.title("🧠 與小Q AI 助教對話")
    for msg, response in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(msg)
        with st.chat_message("assistant"):
            st.markdown(response)

    with st.form("q_form"):
        question = st.text_input("💬 請輸入你想問的問題", key="q_input")
        submitted = st.form_submit_button("送出問題 / Submit")
    if submitted and question.strip():
        result = st.session_state.llm.invoke(f"請針對此問題給出建議或改善方向：{question}")
        st.session_state.chat_history.append((question, result.content))

        try:
            df = pd.read_excel("Database.xlsx")
        except:
            df = pd.DataFrame()

        row = {
            "時間戳記": datetime.now().isoformat(),
            "使用者編號": st.session_state.user_id,
            "語言": st.session_state.language,
            "來源": "小Q",
            "問題": question,
            "AI 回覆": result.content
        }
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_excel("Database.xlsx", index=False)

    st.button("下一頁 / Next", on_click=next_page, key="next_page3")
    st.button("上一頁 / Back", on_click=prev_page, key="back_page3")

# 第 4 頁：ChatGPT 對話內建
elif st.session_state.page == 4:
    st.title("🌍 與 ChatGPT 對話（內建）")
    for msg, reply in st.session_state.chatgpt_history:
        with st.chat_message("user"):
            st.markdown(msg)
        with st.chat_message("assistant"):
            st.markdown(reply)

    with st.form("chatgpt_form"):
        gpt_input = st.text_input("請向 ChatGPT 提問：", key="chatgpt_input")
        gpt_submit = st.form_submit_button("送出問題 / Ask ChatGPT")

    if gpt_submit and gpt_input.strip():
        reply = st.session_state.llm.invoke(f"針對挑戰活動：{st.session_state.activity}，此問題「{gpt_input}」的建議與看法是？")
        st.session_state.chatgpt_history.append((gpt_input, reply.content))

        try:
            df = pd.read_excel("Database.xlsx")
        except:
            df = pd.DataFrame()

        df = pd.concat([df, pd.DataFrame([{
            "時間戳記": datetime.now().isoformat(),
            "使用者編號": st.session_state.user_id,
            "語言": st.session_state.language,
            "來源": "ChatGPT",
            "問題": gpt_input,
            "AI 回覆": reply.content
        }])], ignore_index=True)
        df.to_excel("Database.xlsx", index=False)

    st.button("下一頁 / Next", on_click=next_page, key="next_page4")
    st.button("上一頁 / Back", on_click=prev_page, key="back_page4")
