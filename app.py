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
if 'chatgpt_history' not in st.session_state:
    st.session_state.chatgpt_history = []
if 'llm' not in st.session_state:
    st.session_state.llm = LLM()
if 'language' not in st.session_state:
    st.session_state.language = None

def next_page():
    st.session_state.page += 1

def prev_page():
    st.session_state.page -= 1

# 頁面 1：語言選擇
if st.session_state.page == 1 and st.session_state.language is None:
    st.title("🏁 活動挑戰說明")

    st.session_state.selected_lang = st.selectbox(
        "Choose your language / 選擇語言", ["English", "中文"], key="lang_select"
    )

    if st.button("下一頁 / Next", key="next_page1"):
        st.session_state.language = st.session_state.selected_lang
        st.session_state.page = 2

# 只有當語言選完後才開始其他頁
if st.session_state.language is not None:
    lang_code = 'E' if st.session_state.language == 'English' else 'C'

    # 頁面 2：創意輸入
    if st.session_state.page == 2:
        st.title("💡 初步構想發想")
        activity = st.text_area("請輸入三個最具創意的想法 / Your 3 ideas", key="activity_input")
        if activity:
            st.session_state.activity = activity

        if st.button("下一頁 / Next", key="next_page2"):
            next_page()
        st.button("上一頁 / Back", on_click=prev_page, key="back_page2")

    # 頁面 3：與小Q對話
    elif st.session_state.page == 3:
        st.title("🧠 與小Q AI 助教對話")
        for msg, response in st.session_state.chat_history:
            with st.chat_message("user"):
                st.markdown(msg)
            with st.chat_message("assistant"):
                if response['OUTPUT']['CLS'] == '1':
                    st.markdown(response['OUTPUT']['GUIDE'])
                elif response['OUTPUT']['CLS'] == '2':
                    st.markdown(response['OUTPUT']['EVAL'])
                    st.markdown("**📝 改寫建議：** " + response['OUTPUT']['NEWQ'])

        question = st.text_input("💬 請輸入你想問的問題（輸入 'end' 結束對話）", key="q3_input")
        if st.button("送出問題 / Submit", key="q3_submit"):
            if question.strip().lower() != "end":
                llm_response = st.session_state.llm.Chat(question, lang_code, st.session_state.activity)
                st.session_state.chat_history.append((question, llm_response))
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

    # 頁面 4：內建 ChatGPT 對話頁
    elif st.session_state.page == 4:
        st.title("🌟 與 ChatGPT 對話（內建）")
        for msg, reply in st.session_state.chatgpt_history:
            with st.chat_message("user"):
                st.markdown(msg)
            with st.chat_message("assistant"):
                st.markdown(reply)

        gpt_input = st.text_input("🗨️ 請向 ChatGPT 提出你的問題（輸入 'end' 結束）", key="chatgpt_input")
        if st.button("送出問題 / Ask ChatGPT", key="chatgpt_submit"):
            if gpt_input.strip().lower() != "end":
                response = st.session_state.llm.Chat(gpt_input, lang_code, st.session_state.activity)
                chat_reply = response['OUTPUT']['GUIDE'] or response['OUTPUT']['EVAL'] or "（無回覆）"
                st.session_state.chatgpt_history.append((gpt_input, chat_reply))

                try:
                    df = pd.read_excel("Database.xlsx")
                except:
                    df = pd.DataFrame()

                new_row = {
                    "時間戳記": datetime.now().isoformat(),
                    "使用者編號": st.session_state.user_id,
                    "語言": st.session_state.language,
                    "來源": "ChatGPT頁面",
                    "原始問題": gpt_input,
                    "AI 回應": chat_reply
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_excel("Database.xlsx", index=False)

        st.button("下一頁 / Next", on_click=next_page, key="next_page4")
        st.button("上一頁 / Back", on_click=prev_page, key="back_page4")

# 頁面 5：創意成果輸入
elif st.session_state.page == 5:
    st.title("📝 整合創意成果")
    final_ideas = st.text_area("請輸入你與 ChatGPT 對話後，整理出的三個創意點子", key="final_ideas_input")
    if st.button("送出創意", key="submit_ideas5"):
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

    st.button("下一頁 / Next", on_click=next_page, key="next_page5")
    st.button("上一頁 / Back", on_click=prev_page, key="back_page5")

# 頁面 6：15題問卷 + 開放建議
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

    open_feedback = st.text_area("16. 你還有其他建議或回饋嗎？（非必填）", key="open_feedback")

    if st.button("📩 送出問卷", key="submit_survey6"):
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
