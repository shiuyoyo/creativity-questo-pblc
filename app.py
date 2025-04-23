import streamlit as st
import pandas as pd
from datetime import datetime
from chat import LLM

st.set_page_config(page_title="Questo - Creativity Assistant", layout="centered")

if 'page' not in st.session_state:
    st.session_state.page = 1
if 'user_id' not in st.session_state:
    st.session_state.user_id = f"User_{datetime.now().strftime('%H%M%S')}"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'llm' not in st.session_state:
    st.session_state.llm = LLM()
if 'language' not in st.session_state:
    st.session_state.language = None

def next_page():
    st.session_state.page += 1

def prev_page():
    st.session_state.page -= 1

# 第 1 頁：語言選擇 + 挑戰介紹
if st.session_state.page == 1:
    st.title("🏁 活動挑戰說明")
    st.session_state.language = st.selectbox("Choose your language / 選擇語言", ["English", "中文"], index=0, key="lang_select")
    lang_code = 'E' if st.session_state.language == 'English' else 'C'

    if lang_code == 'E':
        st.markdown("You have joined a competition... Guests include: Business travelers... Old towels to be disposed of...")
    else:
        st.markdown("你要參加一個比賽，是在為一間位於都市商業區的飯店尋找最佳理念...")

    if st.button("下一頁 / Next", key="next_page1"):
        next_page()

lang_code = 'E' if st.session_state.language == 'English' else 'C'

# 第 2 頁：輸入構想
if st.session_state.page == 2:
    st.title("💡 初步構想發想")
    activity = st.text_area("請輸入三個最具創意的想法 / Your 3 ideas", key="activity_input")
    if activity:
        st.session_state.activity = activity

    if st.button("下一頁 / Next", key="next_page2"):
        next_page()
    st.button("上一頁 / Back", on_click=prev_page, key="back_page2")
# 第 3 頁：與小Q AI 對話
elif st.session_state.page == 3:
    st.title("🧠 與小Q AI 助教對話")
    question = st.text_input("請輸入你想問小Q的問題（輸入 'end' 結束對話）", key="question_input")
    if st.button("送出問題 / Submit", key="submit_q3"):
        if question.lower() != "end":
            llm_response = st.session_state.llm.Chat(question, lang_code, st.session_state.activity)
            st.session_state.chat_history.append((question, llm_response))

            with st.chat_message("user"):
                st.write(question)
            with st.chat_message("assistant"):
                if llm_response['OUTPUT']['CLS'] == '1':
                    st.write(llm_response['OUTPUT']['GUIDE'])
                elif llm_response['OUTPUT']['CLS'] == '2':
                    st.write(llm_response['OUTPUT']['EVAL'])
                    st.markdown("**📝 改寫建議：** " + llm_response['OUTPUT']['NEWQ'])

            try:
                df = pd.read_excel("Database.xlsx")
            except:
                df = pd.DataFrame()

            new_row = {
                "時間戳記": datetime.now().isoformat(),
                "使用者編號": st.session_state.user_id,
                "語言": st.session_state.language,
                "原始問題": question,
                "問題類型": llm_response['OUTPUT']['CLS'],
                "AI 回饋": llm_response['OUTPUT']['GUIDE'] or llm_response['OUTPUT']['EVAL'],
                "改寫建議": llm_response['OUTPUT']['NEWQ'],
                "SCAMPER 類型": llm_response['MISC']['SCAMPER_ELEMENT'],
                "成本估算": llm_response['MISC']['cost_input'] + llm_response['MISC']['cost_output']
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_excel("Database.xlsx", index=False)

    st.button("下一頁 / Next", on_click=next_page, key="next_page3")
    st.button("上一頁 / Back", on_click=prev_page, key="back_page3")

# 第 4 頁：ChatGPT 外部互動
elif st.session_state.page == 4:
    st.title("🌍 與 ChatGPT 對話（外部）")
    st.markdown("👉 [點我開啟 ChatGPT 對話頁面](https://chatgpt.com)")
    st.markdown("請與 ChatGPT 對話，獲得靈感後點選下一步")

    st.button("下一頁 / Next", on_click=next_page, key="next_page4")
    st.button("上一頁 / Back", on_click=prev_page, key="back_page4")
