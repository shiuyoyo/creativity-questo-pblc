import streamlit as st
import pandas as pd
from datetime import datetime
from chat import LLM
from openai import OpenAI

st.set_page_config(page_title="Questo - Creativity Assistant", layout="centered")

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
    if lang_code == "E":
        st.title("🏁 Event Challenge Description")
        st.markdown("""You have joined a competition that aims at sourcing the best idea for a hotel located in a business district of an urban city to find good uses of the waste it produces. The hotel is situated next to a hospital, a convention center, and a major tourist attraction.

Guests include: Business travelers, Convention Attendees, Friends and Families of Patients, Tourists

You are required to propose three best ideas for the competition based on old towels to be disposed of.

To win the competition, your ideas should:
- Help transform the waste at the hotel into something that delights the guests
- Be creative

Important Notes:
You do not have to worry about the costs and resources required.
You do not have to delight all types of guests.
""")
    else:
        st.title("🏁 活動挑戰說明")
        st.markdown("""你要參加一個比賽，是在為一間位於都市商業區的飯店尋找最佳理念，找到飯店產生的廢棄物的良好用途。該飯店位於醫院、會議中心和主要旅遊景點旁邊。

其客群主要為：商務旅客、會議參加者、病人的親友、遊客

你需要利用被處理的舊毛巾為比賽提出三個最佳理念。

為了贏得比賽，你的理念應該：
- 幫助將酒店的廢棄物轉化為令客人愉悅的東西
- 富有創意

注意事項：
在此階段，你不必擔心實施的成本和資源。
你不必取悅所有類型的客人。
""")
    st.button("下一頁 / Next", on_click=next_page)

elif st.session_state.page == 2:
    st.title("💡 初步構想發想")
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
    st.title("🧠 與小Q AI 助教對話")

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
    st.title("💬 與 ChatGPT 真實對話")
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

    st.button("下一頁 / Next", on_click=next_page, key="next_page")
    st.button("上一頁 / Back", on_click=prev_page, key="back_page")

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
