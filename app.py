import streamlit as st
import pandas as pd
import os
from datetime import datetime
from langchain_openai import ChatOpenAI

st.set_page_config(page_title="Questo - Creativity Assistant", layout="centered")

# 初始化狀態
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

# 明確指定 OpenAI API Key，並改用 gpt-3.5-turbo

api_key = "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"
if st.session_state.language and 'llm' not in st.session_state:
    api_key = os.environ.get("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")
    st.session_state.llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7,
        openai_api_key=api_key
    )

# 最大頁碼控制
MAX_PAGE = 6
def next_page():
    if st.session_state.page < MAX_PAGE:
        st.session_state.page += 1
def prev_page():
    if st.session_state.page > 1:
        st.session_state.page -= 1

# 語言選擇 + 自動跳頁
if st.session_state.page == 1:
    st.title("🏁 活動挑戰說明")
    if st.session_state.language is None:
        st.session_state.language = st.selectbox("Choose your language / 選擇語言", ["English", "中文"])
        st.session_state.page = 2
        st.rerun()
    else:
        st.markdown(f"🌐 **Current Language**: `{st.session_state.language}`")
        st.stop()

# 顯示語言於每頁頂部
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

# 第 3 頁：小Q AI 助教
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

# 第 4 頁：ChatGPT 內建對話
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

# 第 5 頁：整合創意成果
elif st.session_state.page == 5:
    st.title("📝 整合創意成果")
    final_ideas = st.text_area("請輸入你與 ChatGPT 對話後，整理出的三個創意點子", key="final_ideas_input")
    if st.button("送出創意", key="submit_ideas5"):
        try:
            df = pd.read_excel("Database.xlsx")
        except:
            df = pd.DataFrame()

        row = {
            "時間戳記": datetime.now().isoformat(),
            "使用者編號": st.session_state.user_id,
            "語言": st.session_state.language,
            "來源": "最終創意發想",
            "創意發想結果": final_ideas
        }
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_excel("Database.xlsx", index=False)
        st.success("🎉 創意點子已送出並儲存！")

    st.button("下一頁 / Next", on_click=next_page, key="next_page5")
    st.button("上一頁 / Back", on_click=prev_page, key="back_page5")

# 第 6 頁：體驗問卷
elif st.session_state.page == 6:
    st.title("📋 小Q使用體驗問卷")
    st.markdown("請根據您在這次活動中的經驗，選擇最符合您感受的分數（1 = 非常不同意，5 = 非常同意）")

    questions = [
        "1. 小Q提問助手的介面容易使用",
        "2. 整體互動流程清楚、順暢",
        "3. 小Q的回饋對我有幫助",
        "4. 我會推薦小Q給其他人",
        "5. 與小Q的互動提升了我的創意思考"
    ]

    responses = []
    for i, q in enumerate(questions):
        resp = st.radio(q, [1, 2, 3, 4, 5], horizontal=True, key=f"survey_q{i}")
        responses.append(resp)

    comment = st.text_area("💬 其他建議或感想（非必填）", key="survey_comment")

    if st.button("📩 送出問卷", key="submit_survey"):
        try:
            df = pd.read_excel("Database.xlsx")
        except:
            df = pd.DataFrame()

        result = {
            "時間戳記": datetime.now().isoformat(),
            "使用者編號": st.session_state.user_id,
            "語言": st.session_state.language,
            "來源": "體驗問卷"
        }
        for i, score in enumerate(responses):
            result[f"問卷Q{i+1}"] = score
        result["開放回饋"] = comment

        df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)
        df.to_excel("Database.xlsx", index=False)
        st.success("✅ 感謝您填寫問卷！")
