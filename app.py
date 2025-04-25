import streamlit as st
import pandas as pd
from datetime import datetime
from chat import LLM
from openai import OpenAI
from challenge_page import show_challenge_page
from google_sheet_sync import write_to_google_sheet

st.set_page_config(page_title="Questo - Creativity Assistant", layout="centered")
# 🔁 接收網址中的 page=? 參數
query_params = st.query_params
if "page" in query_params and query_params["page"].isdigit():
    st.session_state.page = int(query_params["page"])
    
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

st.markdown(
    "<div style='text-align: right; font-size: 0.9em;'>🔐 <a href='?page=7'>教師報表頁</a></div>",
    unsafe_allow_html=True
)

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
# 第 5 頁：最終創意發想（不寫入 Excel，只存入 session_state）
elif st.session_state.page == 5:
    if lang_code == "E":
        st.title("📝 Submit Final Creative Ideas")
        final_ideas = st.text_area("Based on your experience and exploration, what are the three most creative ideas you can come up with?")
    else:
        st.title("📝 整合創意成果")
        final_ideas = st.text_area("根據您的體驗與探索，您能想到的三個最具創意的想法是什麼？")

    if st.button("送出 / Submit Final Ideas", key="submit_final_idea"):
        st.session_state.final_idea = final_ideas
        st.success("✅ 最終創意已儲存！請繼續完成問卷")

    st.button("上一頁 / Back", on_click=prev_page, key="back_from_final")
    st.button("下一頁 / Next", on_click=next_page)
# 第 6 頁：體驗問卷 + 資料整合寫入
elif st.session_state.page == 6:
    questions_text = {
        "title": {
            "E": "🎯 Feedback Questionnaire",
            "C": "🎯 小Q體驗問卷調查"
        },
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

    st.title(questions_text["title"][lang_code])
    st.markdown(questions_text["instruction"][lang_code])
    questions = questions_text["questions"][lang_code]

    responses = []
    for i, q in enumerate(questions[:-1]):
        resp = st.radio(q, [1, 2, 3, 4, 5], horizontal=True, key=f"survey_q{i+1}")
        responses.append(resp)

    comment = st.text_area(questions[-1], key="survey_comment")

    if st.button("📩 送出問卷", key="submit_survey_final"):
        try:
            df = pd.read_excel("Database.xlsx")
        except:
            df = pd.DataFrame()

        final_row = {
            "時間戳記": datetime.now().isoformat(),
            "使用者編號": st.session_state.user_id,
            "語言": st.session_state.language,
            "初步構想": st.session_state.get("activity", ""),
            "最終構想": st.session_state.get("final_idea", "")
        }

        # 小Q 對話
        for i, (q, r) in enumerate(st.session_state.get("chat_history", [])):
            final_row[f"小Q 問題{i+1}"] = q
            final_row[f"小Q 回覆{i+1}"] = r['OUTPUT']['GUIDE'] or r['OUTPUT']['EVAL']

        # GPT 對話
        for i, (q, r) in enumerate(st.session_state.get("gpt_chat", [])):
            final_row[f"GPT 問題{i+1}"] = q
            final_row[f"GPT 回覆{i+1}"] = r

        # 問卷結果
        for i, score in enumerate(responses):
            final_row[f"問卷Q{i+1}"] = score
        final_row["開放回饋"] = comment

        df = pd.concat([df, pd.DataFrame([final_row])], ignore_index=True)
        df.to_excel("Database.xlsx", index=False)
        write_to_google_sheet(final_row)
        st.success("✅ 感謝您填寫問卷並完成本次任務！")

# 第 7 頁：教師報表頁
elif st.session_state.page == 7:
    st.title("🔒 教師後台報表")

    PASSWORD = "!@#$123456"
    pw = st.text_input("請輸入教師密碼以檢視報表", type="password", key="admin_pw")

    if pw != PASSWORD:
        st.warning("請輸入正確密碼以進入教師頁面")
        st.stop()

    st.success("登入成功 ✅ 歡迎使用教師報表頁！")

    try:
        df = pd.read_excel("Database.xlsx")
    except:
        st.error("⚠️ 無法讀取資料，請確認是否有正確的 Database.xlsx")
        st.stop()

    if df.empty:
        st.warning("目前尚無任何互動紀錄。請確認至少有一位學生提交過內容。")
    else:
        st.dataframe(df)

        # ✅ 提供 Excel 匯出
        st.download_button("📥 匯出 Excel", data=open("Database.xlsx", "rb").read(), file_name="Database.xlsx")

        # ✅ 匯出 PDF
        from io import BytesIO
        from fpdf import FPDF
        from datetime import datetime

        if st.button("📄 下載整合報表（PDF）", key="dl_pdf"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Creativity Activity Summary Report", ln=True, align="C")
            pdf.ln(10)

            for idx, row in df.iterrows():
                pdf.set_font("Arial", "B", 11)
                pdf.cell(200, 8, f"User ID: {row.get('使用者編號', 'N/A')} | Time: {row.get('時間戳記', '')}", ln=True)
                pdf.set_font("Arial", "", 10)
                for col in df.columns:
                    if col not in ["使用者編號", "時間戳記"]:
                        value = str(row.get(col, "")).replace("\n", "\n")
                        pdf.multi_cell(0, 6, f"{col}: {value}")
                pdf.ln(5)

            buffer = BytesIO()
            pdf.output(buffer)
            pdf_bytes = buffer.getvalue()
            st.download_button("📥 點我下載 PDF", data=pdf_bytes, file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
