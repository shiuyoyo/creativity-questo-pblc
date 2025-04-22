import streamlit as st
import pandas as pd
from datetime import datetime
from chat import LLM

st.set_page_config(page_title="Questo - Creativity Assistant", layout="centered")

# 初始化
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

# 第 1 頁：選擇語言＋活動說明
if st.session_state.page == 1:
    st.title("🏁 活動挑戰說明")
    st.session_state.language = st.selectbox("Choose your language / 選擇語言", ["English", "中文"], index=0)
    lang_code = 'E' if st.session_state.language == 'English' else 'C'

    if lang_code == 'E':
        st.markdown("You have joined a competition... Guests include: Business travelers... Old towels to be disposed of...")
    else:
        st.markdown("你要參加一個比賽，是在為一間位於都市商業區的飯店尋找最佳理念...")

    if st.button("下一頁 / Next"):
        next_page()

# 記住語言
lang_code = 'E' if st.session_state.language == 'English' else 'C'

# 第 2 頁：輸入初步創意
if st.session_state.page == 2:
    st.title("💡 初步構想發想")
    activity = st.text_area("請輸入三個最具創意的想法 / Your 3 ideas")
    if activity:
        st.session_state.activity = activity

    if st.button("下一頁 / Next"):
        next_page()
    st.button("上一頁 / Back", on_click=prev_page)

# 第 3 頁：小Q AI 助教對話
elif st.session_state.page == 3:
    st.title("🧠 與小Q AI 助教對話")
    question = st.text_input("請輸入你想問小Q的問題（輸入 'end' 結束對話）")
    if st.button("送出問題 / Submit"):
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

    st.button("下一頁 / Next", on_click=next_page)
    st.button("上一頁 / Back", on_click=prev_page)

# 第 4 頁：與 ChatGPT 外部對話
elif st.session_state.page == 4:
    st.title("🌍 與 ChatGPT 對話（外部）")
    st.markdown("👉 [點我開啟 ChatGPT 對話頁面](https://chatgpt.com)")
    st.markdown("請與 ChatGPT 對話，獲得靈感後點選下一步")

    st.button("下一頁 / Next", on_click=next_page)
    st.button("上一頁 / Back", on_click=prev_page)

# 第 5 頁：整合創意成果
elif st.session_state.page == 5:
    st.title("📝 整合創意成果")
    final_ideas = st.text_area("請輸入你與 ChatGPT 對話後，整理出的三個創意點子")
    if st.button("送出創意"):
        try:
            df = pd.read_excel("Database.xlsx")
        except:
            df = pd.DataFrame()

        final_row = {
            "時間戳記": datetime.now().isoformat(),
            "使用者編號": st.session_state.user_id,
            "語言": st.session_state.language,
            "創意發想結果": final_ideas
        }
        df = pd.concat([df, pd.DataFrame([final_row])], ignore_index=True)
        df.to_excel("Database.xlsx", index=False)
        st.success("🎉 創意點子已送出並儲存！")

    st.button("下一頁 / Next", on_click=next_page)
    st.button("上一頁 / Back", on_click=prev_page)

# 第 6 頁：問卷
elif st.session_state.page == 6:
    st.title("🎯 小Q體驗問卷調查")
    st.markdown("請根據您在這次活動中的經驗，選擇最符合您感受的分數（1 = 非常不同意，5 = 非常同意）")

    questions = [
        "1. 小Q 提問助手的介面讓我感到容易使用",
        "2. 整體互動流程清楚、順暢",
        "3. 在與小Q的對話過程中，我感到被理解",
        "4. 我知道下一步該做什麼，不感到迷惘",
        "5. 小Q 的回饋對我來說容易理解",
        "6. 小Q 幫助我產生了更多元的想法",
        "7. 小Q 的引導讓我思考到原本沒想到的面向",
        "8. 小Q 的建議對我提問的品質有明顯提升",
        "9. 在與小Q互動後，我對創意挑戰更有信心",
        "10. 小Q 幫助我更明確地聚焦於特定目標對象或情境",
        "11. 我對這次與小Q的互動感到滿意",
        "12. 如果有類似任務，我會願意再次使用小Q",
        "13. 我會推薦小Q給其他同學或朋友使用",
        "14. 小Q 在創意學習中是一個有幫助的工具",
        "15. 整體而言，我的創意思考因為小Q而有所提升"
    ]

    survey_responses = []
    for i, q in enumerate(questions):
        response = st.radio(q, options=[1, 2, 3, 4, 5], key=f"survey_q{i+1}", horizontal=True)
        survey_responses.append(response)

    open_feedback = st.text_area("16. 你還有其他建議或回饋嗎？（非必填）")

    if st.button("📩 送出問卷"):
        try:
            df = pd.read_excel("Database.xlsx")
        except:
            df = pd.DataFrame()

        survey_result = {
            "時間戳記": datetime.now().isoformat(),
            "使用者編號": st.session_state.user_id,
            "語言": st.session_state.language,
        }
        for i, val in enumerate(survey_responses):
            survey_result[f"Q{i+1}"] = val
        survey_result["開放建議"] = open_feedback

        df = pd.concat([df, pd.DataFrame([survey_result])], ignore_index=True)
        df.to_excel("Database.xlsx", index=False)
        st.success("✅ 感謝您完成問卷，資料已儲存！")
