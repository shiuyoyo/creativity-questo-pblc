import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
from openai import OpenAI

from chat import LLM
from challenge_page import show_challenge_page
try:
    from google_sheet_sync import write_to_google_sheet
except Exception as e:
    print("❌ 無法載入 google_sheet_sync:", e)

    def write_to_google_sheet(row_data):
        return False

st.set_page_config(page_title="Questo - Creativity Assistant", layout="centered")

# =========================================================
# 基本設定
# =========================================================
MAX_TURNS = 15
PASSWORD = "!@#$123456"
DB_FILE = "Database.xlsx"

FIXED_COLUMNS = (
    ["時間戳記", "使用者編號", "語言", "初步構想", "最終構想"] +
    [col for i in range(1, MAX_TURNS + 1) for col in [f"小Q 問題{i}", f"小Q 回覆{i}"]] +
    [col for i in range(1, MAX_TURNS + 1) for col in [f"GPT 問題{i}", f"GPT 回覆{i}"]] +
    ["gender", "year_study", "major", "ai_experience"] +
    [f"problem_solving_{i}" for i in range(1, 8)] +
    [f"ai_experience_{i}" for i in range(1, 12)] +
    [f"outcomes_{i}" for i in range(1, 10)] +
    [f"future_{i}" for i in range(1, 3)]
)

# =========================================================
# Query Params
# =========================================================
query_params = st.query_params
if "page" in query_params:
    try:
        st.session_state.page = int(query_params["page"])
    except Exception:
        pass

# =========================================================
# 文字資源
# =========================================================
titles = {
    1: {"E": "🏁 Event Challenge Description", "C": "🏁 活動挑戰說明"},
    2: {"E": "💡 Initial Idea Generation", "C": "💡 初步構想發想"},
    3: {"E": "🧠 Ask AI Assistant – Little Q", "C": "🧠 與Questo AI 助教對話"},
    4: {"E": "💬 Chat with GPT", "C": "💬 與 ChatGPT 真實對話"},
    5: {"E": "📝 Submit Final Creative Ideas", "C": "📝 整合創意成果"},
    6: {"E": "🎯 Feedback Questionnaire", "C": "🎯 小Q體驗問卷調查"},
    7: {"E": "🔒 Teacher Report Dashboard", "C": "🔒 教師後台報表"},
}

ui_texts = {
    "idea_input_label": {
        "E": "To win the competition, what are three of the most creative ideas you can think of?",
        "C": "競賽奪冠：你能想出的三個最具創意的點子是什麼？"
    },
    "idea_warning": {"E": "⚠️ Please enter your ideas first!", "C": "⚠️ 請先輸入構想內容！"},
    "littleq_input_prompt": {
        "E": "Now, you can use our AI Questioning Assistant, called 'Questo', to refine your questioning technique and generate more effective questions. Before you begin, please spend at least 5 minutes using Questo to ask questions related to the challenge of using old hotel towels to delight guests. Instead of providing answers, Questo will offer suggestions and recommendations on how to improve your questions. This will help you learn how to ask better questions and explore different perspectives. You can engage with Questo for as long as you like. When you're ready, click 'Next' to continue. Remember, Questo is designed to help you enhance your questioning skills, which is crucial for creative problem-solving.",
        "C": "現在，你可以使用我們名為「Questo」的 AI 提問助手，來磨練你的提問技巧並產生更有價值的問題。在開始之前，請至少花 5 分鐘使用 Questo，針對「如何利用舊飯店毛巾來驚艷顧客」這個挑戰進行提問。Questo 不會直接給你答案，而是會針對如何改進你的提問方式提供建議與推薦。這將幫助你學習如何提問得更精確，並探索不同的觀點。你可以根據需求與 Questo 進行任何時長的互動。準備好後，請點擊「下一步」繼續。請記住，Questo 旨在幫助你提升提問技巧，而這正是創意解難的關鍵。"
    },
    "littleq_submit_button": {"E": "Submit Question", "C": "送出問題"},
    "littleq_no_response": {"E": "⚠️ Little Q has no suggestions at the moment", "C": "⚠️ 小Q暫時無提供建議"},
    "gpt_input_label": {
        "E": "To spark your imagination, start by asking ChatGPT some questions about the hotel towel challenge below. See what ideas and insights you can gain, then use that inspiration to propose three more creative ideas.",
        "C": "為了激發你的想像力，請先針對下方的飯店毛巾挑戰向 ChatGPT 提出一些問題。看看你能獲得哪些靈感與洞察。"
    },
    "gpt_submit_button": {"E": "Submit to ChatGPT", "C": "送出給 ChatGPT"},
    "gpt_api_error": {"E": "⚠️ Please set OPENAI_API_KEY in Streamlit Secrets", "C": "⚠️ 請在 Streamlit Secrets 設定 OPENAI_API_KEY"},
    "gpt_response_error": {"E": "OpenAI response error: {error}", "C": "OpenAI 回應錯誤：{error}"},
    "gpt_system_prompt": {"E": "You are an AI teaching assistant skilled in guiding creative thinking.", "C": "你是一位擅長引導創意思考的 AI 助教。"},
    "final_idea_prompt": {
        "E": "Based on your experience and exploration, what are the three most creative ideas you can come up with?",
        "C": "根據您的體驗與探索，您能想到的三個最具創意的想法是什麼？"
    },
    "final_idea_submit": {"E": "Submit Final Ideas", "C": "送出最終創意"},
    "final_idea_success": {"E": "✅ Final ideas saved! Please continue to complete the questionnaire", "C": "✅ 最終創意已儲存！請繼續完成問卷"},
    "survey_submit": {"E": "📩 Submit Questionnaire", "C": "📩 送出問卷"},
    "survey_success": {"E": "✅ Thank you for completing the questionnaire and this task!", "C": "✅ 感謝您填寫問卷並完成本次任務！"},
    "survey_backup_warning": {"E": "⚠️ Google Sheet backup failed: {error}", "C": "⚠️ Google Sheet 備份失敗：{error}"},
    "admin_password_prompt": {"E": "Please enter teacher password to view reports", "C": "請輸入教師密碼以檢視報表"},
    "admin_password_warning": {"E": "Please enter the correct password to access teacher page", "C": "請輸入正確密碼以進入教師頁面"},
    "admin_login_success": {"E": "Login successful ✅ Welcome to the teacher report page!", "C": "登入成功 ✅ 歡迎使用教師報表頁！"},
    "admin_no_data_error": {"E": "⚠️ Unable to read data, please confirm Database.xlsx exists", "C": "⚠️ 無法讀取資料，請確認是否有正確的 Database.xlsx"},
    "admin_no_records": {"E": "Currently no interaction records. Please confirm at least one student has submitted content.", "C": "目前尚無任何互動紀錄。請確認至少有一位學生提交過內容。"},
    "admin_export_excel": {"E": "📥 Export Excel", "C": "📥 匯出 Excel"},
    "admin_export_pdf": {"E": "📄 Download Integrated Report (PDF)", "C": "📄 下載整合報表（PDF）"},
    "admin_download_pdf": {"E": "📥 Click to Download PDF", "C": "📥 點我下載 PDF"},
    "next_button": {"E": "Next / 下一頁", "C": "下一頁 / Next"},
    "back_button": {"E": "Back / 上一頁", "C": "上一頁 / Back"}
}

# =========================================================
# Session State 初始化
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = 1
if "user_id" not in st.session_state:
    st.session_state.user_id = f"User_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # [{question, answer}]
if "gpt_chat" not in st.session_state:
    st.session_state.gpt_chat = []      # [{question, answer}]
if "llm" not in st.session_state:
    st.session_state.llm = LLM()
if "language" not in st.session_state:
    st.session_state.language = "English"
if "activity_warning" not in st.session_state:
    st.session_state.activity_warning = False
if "final_idea" not in st.session_state:
    st.session_state.final_idea = ""
if "activity" not in st.session_state:
    st.session_state.activity = ""

lang_code = "E" if st.session_state.language == "English" else "C"

# =========================================================
# 工具函式
# =========================================================
def next_page():
    st.session_state.page += 1


def prev_page():
    st.session_state.page -= 1


def ensure_database_file():
    try:
        df = pd.read_excel(DB_FILE)
    except Exception:
        df = pd.DataFrame(columns=FIXED_COLUMNS)

    for col in FIXED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[FIXED_COLUMNS]
    return df


def build_final_row(responses: dict):
    final_row = {col: "" for col in FIXED_COLUMNS}
    final_row["時間戳記"] = datetime.now().isoformat()
    final_row["使用者編號"] = st.session_state.user_id
    final_row["語言"] = st.session_state.language
    final_row["初步構想"] = st.session_state.get("activity", "")
    final_row["最終構想"] = st.session_state.get("final_idea", "")

    for i, item in enumerate(st.session_state.get("chat_history", [])[:MAX_TURNS], start=1):
        final_row[f"小Q 問題{i}"] = item.get("question", "")
        final_row[f"小Q 回覆{i}"] = item.get("answer", "")

    for i, item in enumerate(st.session_state.get("gpt_chat", [])[:MAX_TURNS], start=1):
        final_row[f"GPT 問題{i}"] = item.get("question", "")
        final_row[f"GPT 回覆{i}"] = item.get("answer", "")

    final_row.update(responses)
    return final_row


def save_row_to_excel(final_row: dict):
    df = ensure_database_file()
    new_df = pd.DataFrame([final_row], columns=FIXED_COLUMNS)
    df = pd.concat([df, new_df], ignore_index=True)
    df.to_excel(DB_FILE, index=False)


def build_pdf_bytes(df: pd.DataFrame):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)

    for _, row in df.iterrows():
        pdf.add_page()
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, txt="Creativity Activity Summary Report", ln=True)
        pdf.ln(2)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 7, txt=f"User ID: {row.get('使用者編號', '')}", ln=True)
        pdf.cell(0, 7, txt=f"Time: {str(row.get('時間戳記', ''))}", ln=True)
        pdf.ln(2)

        for col in df.columns:
            if col in ["使用者編號", "時間戳記"]:
                continue
            value = str(row.get(col, ""))
            safe_text = f"{col}: {value}".encode("latin-1", "replace").decode("latin-1")
            pdf.multi_cell(0, 6, txt=safe_text)
        pdf.ln(3)

    return bytes(pdf.output(dest="S"))


# =========================================================
# 頂部區域
# =========================================================
st.markdown(
    "<div style='text-align: right; font-size: 0.9em;'>🔐 <a href='?page=7'>教師報表頁</a></div>",
    unsafe_allow_html=True
)

selected_lang = st.selectbox(
    "Choose your language / 選擇語言",
    ["English", "中文"],
    index=0 if st.session_state.language == "English" else 1,
    key="language_selector",
    disabled=(st.session_state.page > 1)
)
st.session_state.language = selected_lang
lang_code = "E" if st.session_state.language == "English" else "C"

# =========================================================
# Page 1: 活動說明
# =========================================================
if st.session_state.page == 1:
    show_challenge_page(lang_code, next_page)
    st.button(ui_texts["next_button"][lang_code], on_click=next_page)

# =========================================================
# Page 2: 初步構想
# =========================================================
elif st.session_state.page == 2:
    st.title(titles[2][lang_code])
    activity = st.text_area(
        ui_texts["idea_input_label"][lang_code],
        value=st.session_state.get("activity", "")
    )

    if activity.strip():
        st.session_state.activity_warning = False

    col1, col2 = st.columns(2)
    with col1:
        st.button(ui_texts["back_button"][lang_code], on_click=prev_page)
    with col2:
        if st.button(ui_texts["next_button"][lang_code]):
            if not activity.strip():
                st.session_state.activity_warning = True
            else:
                st.session_state.activity = activity.strip()
                st.session_state.llm.setup_language_and_activity(lang_code, st.session_state.activity)
                next_page()

    if st.session_state.activity_warning:
        st.warning(ui_texts["idea_warning"][lang_code])

# =========================================================
# Page 3: 小Q 對話
# =========================================================
elif st.session_state.page == 3:
    st.title(titles[3][lang_code])

    for item in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(item["question"])
        with st.chat_message("assistant"):
            answer = item["answer"].strip() if item["answer"] else ""
            st.write(answer if answer else ui_texts["littleq_no_response"][lang_code])

    with st.form("littleq_form"):
        question = st.text_input(ui_texts["littleq_input_prompt"][lang_code], key="input_q")
        submitted = st.form_submit_button(ui_texts["littleq_submit_button"][lang_code])

    if submitted and question.strip():
        llm_response = st.session_state.llm.Chat(question.strip(), lang_code, st.session_state.activity)
        answer = ""
        try:
            answer = (llm_response.get("OUTPUT", {}).get("GUIDE", "") or
                      llm_response.get("OUTPUT", {}).get("EVAL", "") or "")
        except Exception:
            answer = ""

        st.session_state.chat_history.append({
            "question": question.strip(),
            "answer": answer.strip()
        })
        st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        st.button(ui_texts["back_button"][lang_code], on_click=prev_page)
    with col2:
        st.button(ui_texts["next_button"][lang_code], on_click=next_page)

# =========================================================
# Page 4: GPT 對話
# =========================================================
elif st.session_state.page == 4:
    st.title(titles[4][lang_code])

    for item in st.session_state.gpt_chat:
        with st.chat_message("user"):
            st.write(item["question"])
        with st.chat_message("assistant"):
            st.write(item["answer"])

    with st.form("gpt_form"):
        msg = st.text_input(ui_texts["gpt_input_label"][lang_code], key="gpt_input")
        submitted_gpt = st.form_submit_button(ui_texts["gpt_submit_button"][lang_code])

    if submitted_gpt and msg.strip():
        if "OPENAI_API_KEY" not in st.secrets:
            st.error(ui_texts["gpt_api_error"][lang_code])
        else:
            try:
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                history = [{"role": "system", "content": ui_texts["gpt_system_prompt"][lang_code]}]
                for item in st.session_state.gpt_chat:
                    history.append({"role": "user", "content": item["question"]})
                    history.append({"role": "assistant", "content": item["answer"]})
                history.append({"role": "user", "content": msg.strip()})

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=history
                )
                reply = response.choices[0].message.content.strip()

                st.session_state.gpt_chat.append({
                    "question": msg.strip(),
                    "answer": reply
                })
                st.rerun()
            except Exception as e:
                st.error(ui_texts["gpt_response_error"][lang_code].format(error=e))

    col1, col2 = st.columns(2)
    with col1:
        st.button(ui_texts["back_button"][lang_code], on_click=prev_page)
    with col2:
        st.button(ui_texts["next_button"][lang_code], on_click=next_page)

# =========================================================
# Page 5: 最終創意
# =========================================================
elif st.session_state.page == 5:
    st.title(titles[5][lang_code])

    final_ideas = st.text_area(
        ui_texts["final_idea_prompt"][lang_code],
        value=st.session_state.get("final_idea", "")
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.button(ui_texts["back_button"][lang_code], on_click=prev_page)
    with col2:
        if st.button(ui_texts["final_idea_submit"][lang_code], key="submit_final_idea"):
            st.session_state.final_idea = final_ideas.strip()
            st.success(ui_texts["final_idea_success"][lang_code])
    with col3:
        st.button(ui_texts["next_button"][lang_code], on_click=next_page)

# =========================================================
# Page 6: 問卷 + 寫入 Excel
# =========================================================
elif st.session_state.page == 6:
    questionnaire_data = {
        "title": {"E": "🎯 Research Questionnaire", "C": "🎯 研究問卷調查"},
        "scale_options": {
            "E": [
                "1: Strongly disagree", "2: Disagree", "3: Slightly disagree",
                "4: Neutral", "5: Slightly agree", "6: Agree", "7: Strongly agree"
            ],
            "C": [
                "1: 非常不同意", "2: 不同意", "3: 有點不同意",
                "4: 普通", "5: 有點同意", "6: 同意", "7: 非常同意"
            ]
        },
        "sections": {
            "E": {
                "demographics": {
                    "title": "Section 1: Demographics",
                    "questions": [
                        {"text": "Gender:", "type": "radio", "options": ["Male", "Female", "Prefer not to say"], "key": "gender"},
                        {"text": "Year of Study:", "type": "radio", "options": ["2nd Year", "3rd Year", "4th Year", "Graduate"], "key": "year_study"},
                        {"text": "Major:", "type": "radio", "options": ["College of Hospitality", "College of Tourism", "College of Culinary Arts", "College of International Studies", "Other"], "key": "major"},
                        {"text": "Prior Experience with Generative AI:", "type": "radio", "options": ["Never used", "Novice", "Intermediate", "Advanced"], "key": "ai_experience"}
                    ]
                },
                "problem_solving": {
                    "title": "Section 2: Your Problem-Solving Style",
                    "questions": [
                        "I feel that I am good at generating novel ideas for hospitality problems.",
                        "I have confidence in my ability to solve problems creatively.",
                        "I have a knack for further developing the ideas of others.",
                        "To ensure that you are paying attention to the questions, please select \"Strongly Disagree\" (1) for this item.",
                        "I am good at finding creative solutions to complex problems.",
                        "I suggest new ways to achieve goals or objectives.",
                        "I feel confident in my ability to ask insightful questions."
                    ]
                },
                "ai_experience_section": {
                    "title": "Section 3: Your Experience Using the AI Tool",
                    "questions": [
                        "Using Questo improves my performance in solving the assigned case study.",
                        "Questo enables me to formulate questions more quickly than I could alone.",
                        "I find Questo useful for generating a wider variety of questions.",
                        "Using Questo makes it easier to understand the core problem.",
                        "Overall, I find Questo to be useful in my learning process.",
                        "My interaction with the AI Questioning Support Tool is clear and understandable.",
                        "It is easy for me to become skillful at using Questo.",
                        "Technology in hospitality is advancing rapidly. To show that you are reading the statements carefully, please ignore the scale and select \"Neutral\" (4) for this question.",
                        "I find Questo easy to interact with (e.g., the chat interface is intuitive).",
                        "Getting Questo to provide the help I needed was easy.",
                        "I did not require a lot of mental effort to learn how to operate Questo."
                    ]
                },
                "outcomes": {
                    "title": "Section 4: Project Outcomes & Reflection",
                    "questions": [
                        "Questo helped me generate a large number of questions regarding the problem.",
                        "I was able to come up with more solutions than usual with the help of Questo.",
                        "Questo helped me see the problem from different angles/perspectives.",
                        "Questo's suggestions helped me break away from my initial, fixed assumptions.",
                        "In order to verify the quality of our data, please select \"Strongly Agree\" (7) for this statement.",
                        "I was able to switch between different types of questions (e.g., strategic vs. operational) easily.",
                        "The questions I formulated with Questo were unique and innovative.",
                        "Questo helped me discover ideas I would never have thought of on my own.",
                        "The final solution I proposed was novel compared to standard solutions."
                    ]
                },
                "future": {
                    "title": "Section 5: Future Outlook",
                    "questions": [
                        "Assuming I have access to this AI tool, I intend to use it for future class assignments.",
                        "I would recommend this AI Questioning Support Tool to other hospitality students."
                    ]
                }
            },
            "C": {
                "demographics": {
                    "title": "第一部分：基本資料",
                    "questions": [
                        {"text": "生理性別：", "type": "radio", "options": ["男", "女", "不願透露"], "key": "gender"},
                        {"text": "年級：", "type": "radio", "options": ["大二", "大三", "大四", "研究所"], "key": "year_study"},
                        {"text": "主修科系：", "type": "radio", "options": ["餐旅學院", "觀光學院", "廚藝學院", "國際學院", "其他"], "key": "major"},
                        {"text": "生成式 AI (如 ChatGPT) 使用經驗：", "type": "radio", "options": ["從未用過", "初學者 (偶爾嘗試)", "中等程度 (曾用於作業或日常事務)", "進階使用者 (經常使用並熟悉提示詞技巧)"], "key": "ai_experience"}
                    ]
                },
                "problem_solving": {
                    "title": "第二部分：您的問題解決風格",
                    "questions": [
                        "覺得自己擅長針對餐旅業的問題提出新穎的想法。",
                        "我有信心能創造性地解決問題。",
                        "我擅長延伸或進一步發展他人的想法。",
                        "為了確保您有仔細閱讀題目，請在本題選擇「非常不同意」(1)。",
                        "我擅長為複雜的問題找到創新的解決方案。",
                        "我會提出新的方法來達成目標。",
                        "我有信心能提出具洞察力的問題。"
                    ]
                },
                "ai_experience_section": {
                    "title": "第三部分：您使用 AI 工具的經驗",
                    "questions": [
                        "使用小Q改善了我解決個案研究的表現。",
                        "這個小Q讓我能比自己單獨作業時更快擬定問題。",
                        "我發現小Q對於產生「更多樣化」的問題很有用。",
                        "使用小Q讓我更容易理解核心問題所在。",
                        "整體而言，我覺得小Q對我的學習過程很有用。",
                        "我與小Q的互動過程是清晰易懂的。",
                        "我很容易就能熟練地使用小Q。",
                        "餐旅業的科技發展相當迅速。為了證明您有詳閱這些敘述，請忽略量表選項，直接在本題選擇「普通」(4)。",
                        "我覺得小Q很容易互動（例如：聊天介面很直觀）。",
                        "我能輕鬆透過小Q獲得我需要的協助。",
                        "我不需要花費太多心力去學習如何操作小Q。"
                    ]
                },
                "outcomes": {
                    "title": "第四部分：成果與反思",
                    "questions": [
                        "小Q幫助我針對問題產生了大量的提問（流暢力）。",
                        "在小Q的協助下，我能比平常提出更多的解決方案。",
                        "小Q幫助我從不同的角度或觀點來看待問題（變通力）。",
                        "小Q的建議幫助我打破了最初的既定假設或固著觀點。",
                        "為了驗證我們資料的品質，請在本題直接選擇「非常同意」(7)。",
                        "我能輕鬆地在不同類型的問題（例如：策略性 vs. 營運性）之間切換。",
                        "我透過小Q擬定的問題是獨特且創新的（獨創力）。",
                        "小Q幫助我發現了一些我自己絕對想不到的想法。",
                        "與標準答案相比，我提出的最終解決方案相當新穎。"
                    ]
                },
                "future": {
                    "title": "第五部分：未來展望",
                    "questions": [
                        "假設我能使用小Q，我打算在未來的課堂作業中使用它。",
                        "我會向其他餐旅系學生推薦小Q。"
                    ]
                }
            }
        }
    }

    st.title(questionnaire_data["title"][lang_code])
    st.markdown(f"**Scale: {' | '.join(questionnaire_data['scale_options'][lang_code])}**")

    responses = {}
    scale_options = questionnaire_data["scale_options"][lang_code]
    sec = questionnaire_data["sections"][lang_code]

    st.subheader(sec["demographics"]["title"])
    for q_data in sec["demographics"]["questions"]:
        responses[q_data["key"]] = st.radio(q_data["text"], q_data["options"], key=f"demo_{q_data['key']}")

    st.subheader(sec["problem_solving"]["title"])
    for i, question in enumerate(sec["problem_solving"]["questions"], start=1):
        selected_option = st.radio(question, scale_options, key=f"ps_{i}")
        responses[f"problem_solving_{i}"] = int(selected_option.split(":")[0])

    st.subheader(sec["ai_experience_section"]["title"])
    for i, question in enumerate(sec["ai_experience_section"]["questions"], start=1):
        selected_option = st.radio(question, scale_options, key=f"ai_exp_{i}")
        responses[f"ai_experience_{i}"] = int(selected_option.split(":")[0])

    st.subheader(sec["outcomes"]["title"])
    for i, question in enumerate(sec["outcomes"]["questions"], start=1):
        selected_option = st.radio(question, scale_options, key=f"outcomes_{i}")
        responses[f"outcomes_{i}"] = int(selected_option.split(":")[0])

    st.subheader(sec["future"]["title"])
    for i, question in enumerate(sec["future"]["questions"], start=1):
        selected_option = st.radio(question, scale_options, key=f"future_{i}")
        responses[f"future_{i}"] = int(selected_option.split(":")[0])

    col1, col2 = st.columns(2)
    with col1:
        st.button(ui_texts["back_button"][lang_code], on_click=prev_page)
    with col2:
        if st.button(ui_texts["survey_submit"][lang_code], key="submit_survey_final"):
            final_row = build_final_row(responses)

            # 先存 Excel
            save_row_to_excel(final_row)
            st.success(ui_texts["survey_success"][lang_code])

            # 再備份 Google Sheet
            backup_success = write_to_google_sheet(final_row)
            if not backup_success:
                st.warning(
                    ui_texts["survey_backup_warning"][lang_code].format(
                        error="Google Sheet backup failed, but Excel was saved successfully."
                    )
                )

# =========================================================
# Page 7: 教師後台
# =========================================================
elif st.session_state.page == 7:
    st.title(titles[7][lang_code])
    pw = st.text_input(ui_texts["admin_password_prompt"][lang_code], type="password", key="admin_pw")

    if pw != PASSWORD:
        st.warning(ui_texts["admin_password_warning"][lang_code])
        st.stop()

    st.success(ui_texts["admin_login_success"][lang_code])

    try:
        df = ensure_database_file()
    except Exception:
        st.error(ui_texts["admin_no_data_error"][lang_code])
        st.stop()

    if df.empty:
        st.warning(ui_texts["admin_no_records"][lang_code])
    else:
        qa_cols = (
            ["時間戳記", "使用者編號", "語言", "初步構想", "最終構想"] +
            [f"小Q 問題{i}" for i in range(1, 16)] +
            [f"小Q 回覆{i}" for i in range(1, 16)] +
            [f"GPT 問題{i}" for i in range(1, 16)] +
            [f"GPT 回覆{i}" for i in range(1, 16)]
        )
        show_cols = [col for col in qa_cols if col in df.columns]
        st.dataframe(df[show_cols], use_container_width=True)

        with open(DB_FILE, "rb") as f:
            st.download_button(
                ui_texts["admin_export_excel"][lang_code],
                data=f.read(),
                file_name="Database.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        if st.button(ui_texts["admin_export_pdf"][lang_code], key="dl_pdf"):
            pdf_bytes = build_pdf_bytes(df)
            st.download_button(
                ui_texts["admin_download_pdf"][lang_code],
                data=pdf_bytes,
                file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )
