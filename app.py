import streamlit as st
import pandas as pd
from datetime import datetime
from chat import LLM
from openai import OpenAI
from challenge_page import show_challenge_page

st.set_page_config(page_title="Questo - Creativity Assistant", layout="centered")
titles = {
    1: {"E": "🏁 Event Challenge Description", "C": "🏁 活動挑戰說明"},
    2: {"E": "💡 Initial Idea Generation", "C": "💡 初步構想發想"},
    3: {"E": "🧠 Ask AI Assistant – Little Q", "C": "🧠 與小Q AI 助教對話"},
    4: {"E": "💬 Chat with GPT", "C": "💬 與 ChatGPT 真實對話"},
    5: {"E": "📝 Submit Final Creative Ideas", "C": "📝 整合創意成果"},
    6: {"E": "🎯 Feedback Questionnaire", "C": "🎯 小Q體驗問卷調查"},
}

questions_text = {
    "instruction": {
        "E": "Based on your experience with this activity, choose the score that best represents your feelings. (1 = Strongly Disagree, 5 = Strongly Agree)",
        "C": "請根據您在這次活動中的經驗，選擇最符合您感受的分數（1 = 非常不同意，5 = 非常同意）"
    },
    "questions": {
        "E": [
            "I found Little Q easy to use.",
            "The interaction flow was smooth and clear.",
            "Little Q's feedback was helpful.",
            "I would recommend Little Q to others.",
            "The interaction helped me think more creatively.",
            "Other comments or suggestions (optional)"
        ],
        "C": [
            "小Q提問助手的介面容易使用",
            "整體互動流程清楚、順暢",
            "小Q的回饋對我有幫助",
            "我會推薦小Q給其他人",
            "與小Q的互動提升了我的創意思考",
            "其他建議或意見（非必填）"
        ]
    }
}

if 'page' not in st.session_state:
    st.session_state.page = 1
if 'user_id' not in st.session_state:
    st.session_state.user_id = f"User_{datetime.now().strftime('%H%M%S')}"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'gpt_chat' not in st.session_state:
    st.session_state.gpt_chat = []
if 'llm' not in st.session_state:
    st.session_state.llm = LLM()
if 'language' not in st.session_state:
    st.session_state.language = "English"

st.selectbox(
    "Choose your language / 選擇語言",
    ["English", "中文"],
    index=0 if st.session_state.language == "English" else 1,
    key="language",
    disabled=(st.session_state.page > 1)
)

lang_code = "E" if st.session_state.language == "English" else "C"

def next_page():
    st.session_state.page += 1
def prev_page():
    st.session_state.page -= 1

if st.session_state.page == 1:
    show_challenge_page(lang_code, next_page)
    
    st.button("下一頁 / Next", on_click=next_page)

elif st.session_state.page == 2:
    st.title(titles[st.session_state.page][lang_code])
    if 'activity_warning' not in st.session_state:
        st.session_state.activity_warning = False

    activity = st.text_area("請輸入三個最具創意的想法 / Your 3 ideas", value=st.session_state.get("activity", ""))
    if activity.strip():
        st.session_state.activity_warning = False

    if st.button("下一頁 / Next"):
        if activity.strip() == "":
            st.session_state.activity_warning = True
        else:
            st.session_state.activity = activity
            st.session_state.llm.setup_language_and_activity(lang_code, activity)
            next_page()

    if st.session_state.activity_warning:
        st.warning("⚠️ 請先輸入構想內容！")

    st.button("上一頁 / Back", on_click=prev_page)

elif st.session_state.page == 3:
    st.title(titles[st.session_state.page][lang_code])

    for q, r in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(q)
        with st.chat_message("assistant"):
            reply = r['OUTPUT']['GUIDE'] or r['OUTPUT']['EVAL']
            st.write(reply if reply.strip() else "⚠️ 小Q暫時無提供建議")

    with st.form("question_form"):
        question = st.text_input("請輸入你想問小Q的問題（輸入 'end' 結束對話）", key="input_q")
        submitted = st.form_submit_button("送出問題 / Submit")

        if submitted and question.strip() and question.lower() != "end":
            llm_response = st.session_state.llm.Chat(question, lang_code, st.session_state.activity)
            st.session_state.chat_history.append((question, llm_response))
            st.rerun()  # ← 加入這行確保立即更新畫面
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

elif st.session_state.page == 4:
    st.title(titles[st.session_state.page][lang_code])
    msg = st.text_input("輸入你的問題給 ChatGPT", key="gpt_input")
    if st.button("送出給 ChatGPT"):
        if "OPENAI_API_KEY" not in st.secrets:
            st.error("⚠️ 請在 Streamlit Secrets 設定 OPENAI_API_KEY")
        else:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "你是一位擅長引導創意思考的 AI 助教"},
                        {"role": "user", "content": msg}
                    ]
                )
                reply = response.choices[0].message.content
                st.session_state.gpt_chat.append(("user", msg))
                st.session_state.gpt_chat.append(("gpt", reply))
            except Exception as e:
                st.error(f"OpenAI 回應錯誤：{e}")

    for role, txt in st.session_state.gpt_chat:
        with st.chat_message("user" if role == "user" else "assistant"):
            st.write(txt)

    st.button("下一頁 / Next", on_click=next_page)
    st.button("上一頁 / Back", on_click=prev_page)
# 第 5 頁：整合創意成果
elif st.session_state.page == 5:
    st.title(titles[st.session_state.page][lang_code])
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

    st.button("下一頁 / Next", on_click=next_page, key="next_page")
    st.button("上一頁 / Back", on_click=prev_page, key="back_page")

# 第 6 頁：體驗問卷
elif st.session_state.page == 6:
    st.title(titles[st.session_state.page][lang_code])
     st.markdown(questions_text["instruction"][lang_code])
    questions = questions_text["questions"][lang_code]

    responses = []
    for i, q in enumerate(questions[:-1]):
        resp = st.radio(q, [1, 2, 3, 4, 5], horizontal=True, key=f"survey_q{i+1}")
        responses.append(resp)

    comment = st.text_area(questions[-1], key="survey_comment")

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
