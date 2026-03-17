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
    3: {"E": "🧠 Ask AI Assistant – Little Q", "C": "🧠 與Questo AI 助教對話"},
    4: {"E": "💬 Chat with GPT", "C": "💬 與 ChatGPT 真實對話"},
    5: {"E": "📝 Submit Final Creative Ideas", "C": "📝 整合創意成果"},
    6: {"E": "🎯 Feedback Questionnaire", "C": "🎯 小Q體驗問卷調查"},
}

# ✅ 完整的語言文字字典
ui_texts = {
    # 第2頁 - 初步構想
    "idea_input_label": {
        "E": "To win the competition, what are three of the most creative ideas you can think of?",
        "C": "競賽奪冠：你能想出的三個最具創意的點子是什麼？"
    },
    "idea_warning": {
        "E": "⚠️ Please enter your ideas first!",
        "C": "⚠️ 請先輸入構想內容！"
    },
    
    # 第3頁 - 小Q對話
    "littleq_input_prompt": {
        "E": "Now, you can use our AI Questioning Assistant, called 'Questo', to refine your questioning technique and generate more effective questions.Before you begin, please spend at least 5 minutes using Questo to ask questions related to the challenge of using old hotel towels to delight guests. Instead of providing answers, Questo will offer suggestions and recommendations on how to improve your questions. This will help you learn how to ask better questions and explore different perspectives. You can engage with Questo for as long as you like. When you're ready, click 'Next' to continue. Remember, Questo is designed to help you enhance your questioning skills, which is crucial for creative problem-solving.",
        "C": "現在，你可以使用我們名為 「Questo」 的 AI 提問助手，來磨練你的提問技巧並產生更有價值的問題。在開始之前，請至少花 5 分鐘 使用 Questo，針對**「如何利用舊飯店毛巾來驚艷顧客」**這個挑戰進行提問。Questo 不會直接給你答案，而是會針對如何改進你的提問方式提供建議與推薦。這將幫助你學習如何提問得更精確，並探索不同的觀點。你可以根據需求與 Questo 進行任何時長的互動。準備好後，請點擊「下一步」繼續。請記住，Questo 旨在幫助你提升提問技巧，而這正是創意解難（Creative Problem-solving）的關鍵。"
    },
    "littleq_submit_button": {
        "E": "Submit Question",
        "C": "送出問題"
    },
    "littleq_no_response": {
        "E": "⚠️ Little Q has no suggestions at the moment",
        "C": "⚠️ 小Q暫時無提供建議"
    },
    
    # 第4頁 - ChatGPT對話
    "gpt_input_label": {
        "E": "To spark your imagination, start by asking ChatGPT some questions about the hotel towel challenge below. See what ideas and insights you can gain, then use that inspiration to propose three more creative ideas.",
        "C": "為了激發你的想像力，請先針對下方的飯店毛巾挑戰向 ChatGPT 提出一些問題。看看你能獲得哪些靈感與洞察."
    },
    "gpt_submit_button": {
        "E": "Submit to ChatGPT",
        "C": "送出給 ChatGPT"
    },
    "gpt_api_error": {
        "E": "⚠️ Please set OPENAI_API_KEY in Streamlit Secrets",
        "C": "⚠️ 請在 Streamlit Secrets 設定 OPENAI_API_KEY"
    },
    "gpt_response_error": {
        "E": "OpenAI response error: {error}",
        "C": "OpenAI 回應錯誤：{error}"
    },
    "gpt_system_prompt": {
        "E": "You are an AI teaching assistant skilled in guiding creative thinking",
        "C": "你是一位擅長引導創意思考的 AI 助教"
    },
    
    # 第5頁 - 最終創意
    "final_idea_prompt": {
        "E": "Based on your experience and exploration, what are the three most creative ideas you can come up with?",
        "C": "根據您的體驗與探索，您能想到的三個最具創意的想法是什麼？"
    },
    "final_idea_submit": {
        "E": "Submit Final Ideas",
        "C": "送出最終創意"
    },
    "final_idea_success": {
        "E": "✅ Final ideas saved! Please continue to complete the questionnaire",
        "C": "✅ 最終創意已儲存！請繼續完成問卷"
    },
    
    # 第6頁 - 問卷
    "survey_submit": {
        "E": "📩 Submit Questionnaire",
        "C": "📩 送出問卷"
    },
    "survey_success": {
        "E": "✅ Thank you for completing the questionnaire and this task!",
        "C": "✅ 感謝您填寫問卷並完成本次任務！"
    },
    "survey_backup_warning": {
        "E": "⚠️ Google Sheet backup failed: {error}",
        "C": "⚠️ Google Sheet 備份失敗：{error}"
    },
    
    # 第7頁 - 教師報表
    "admin_title": {
        "E": "🔒 Teacher Report Dashboard",
        "C": "🔒 教師後台報表"
    },
    "admin_password_prompt": {
        "E": "Please enter teacher password to view reports",
        "C": "請輸入教師密碼以檢視報表"
    },
    "admin_password_warning": {
        "E": "Please enter the correct password to access teacher page",
        "C": "請輸入正確密碼以進入教師頁面"
    },
    "admin_login_success": {
        "E": "Login successful ✅ Welcome to the teacher report page!",
        "C": "登入成功 ✅ 歡迎使用教師報表頁！"
    },
    "admin_no_data_error": {
        "E": "⚠️ Unable to read data, please confirm Database.xlsx exists",
        "C": "⚠️ 無法讀取資料，請確認是否有正確的 Database.xlsx"
    },
    "admin_no_records": {
        "E": "Currently no interaction records. Please confirm at least one student has submitted content.",
        "C": "目前尚無任何互動紀錄。請確認至少有一位學生提交過內容。"
    },
    "admin_export_excel": {
        "E": "📥 Export Excel",
        "C": "📥 匯出 Excel"
    },
    "admin_export_pdf": {
        "E": "📄 Download Integrated Report (PDF)",
        "C": "📄 下載整合報表（PDF）"
    },
    "admin_download_pdf": {
        "E": "📥 Click to Download PDF",
        "C": "📥 點我下載 PDF"
    },
    
    # 通用按鈕
    "next_button": {
        "E": "Next",
        "C": "下一頁"
    },
    "back_button": {
        "E": "Back", 
        "C": "上一頁"
    },
    "next_back_button": {
        "E": "Next / 下一頁",
        "C": "下一頁 / Next"
    },
    "back_next_button": {
        "E": "Back / 上一頁",
        "C": "上一頁 / Back"
    }
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
if 'maintenance_mode' not in st.session_state:
    st.session_state.maintenance_mode = False  # ✅ 加入維護模式開關

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

    activity = st.text_area(ui_texts["idea_input_label"][lang_code], value=st.session_state.get("activity", ""))
    if activity.strip():
        st.session_state.activity_warning = False

    if st.button(ui_texts["next_back_button"][lang_code]):
        if activity.strip() == "":
            st.session_state.activity_warning = True
        else:
            st.session_state.activity = activity
            st.session_state.llm.setup_language_and_activity(lang_code, activity)
            next_page()

    if st.session_state.activity_warning:
        st.warning(ui_texts["idea_warning"][lang_code])

    st.button(ui_texts["back_next_button"][lang_code], on_click=prev_page)

elif st.session_state.page == 3:
    st.title(titles[st.session_state.page][lang_code])

    for q, r in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(q)
        with st.chat_message("assistant"):
            reply = r['OUTPUT']['GUIDE'] or r['OUTPUT']['EVAL']
            st.write(reply if reply.strip() else ui_texts["littleq_no_response"][lang_code])

    with st.form("question_form"):
        # ✅ 修正：使用動態語言文字
        question = st.text_input(ui_texts["littleq_input_prompt"][lang_code], key="input_q")
        submitted = st.form_submit_button(f"{ui_texts['littleq_submit_button'][lang_code]} / Submit")

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

    # ✅ 修正：使用動態語言文字
    st.button(ui_texts["next_back_button"][lang_code], on_click=next_page)
    st.button(ui_texts["back_next_button"][lang_code], on_click=prev_page)

elif st.session_state.page == 4:
    st.title(titles[st.session_state.page][lang_code])
    msg = st.text_input(ui_texts["gpt_input_label"][lang_code], key="gpt_input")
    if st.button(ui_texts["gpt_submit_button"][lang_code]):
        if "OPENAI_API_KEY" not in st.secrets:
            st.error(ui_texts["gpt_api_error"][lang_code])
        else:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            try:
                history = [{"role": "system", "content": ui_texts["gpt_system_prompt"][lang_code]}]
                for role, txt in st.session_state.gpt_chat:
                    history.append({"role": "user" if role == "user" else "assistant", "content": txt})
                history.append({"role": "user", "content": msg})
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=history
                )
                reply = response.choices[0].message.content
                st.session_state.gpt_chat.append(("user", msg))
                st.session_state.gpt_chat.append(("gpt", reply))
            except Exception as e:
                st.error(ui_texts["gpt_response_error"][lang_code].format(error=e))

    for role, txt in st.session_state.gpt_chat:
        with st.chat_message("user" if role == "user" else "assistant"):
            st.write(txt)

    st.button(ui_texts["next_back_button"][lang_code], on_click=next_page)
    st.button(ui_texts["back_next_button"][lang_code], on_click=prev_page)
# 第 5 頁：最終創意發想（不寫入 Excel，只存入 session_state）
elif st.session_state.page == 5:
    st.title(titles[st.session_state.page][lang_code])
    final_ideas = st.text_area(ui_texts["final_idea_prompt"][lang_code])

    if st.button(f"{ui_texts['final_idea_submit'][lang_code]} / Submit Final Ideas", key="submit_final_idea"):
        st.session_state.final_idea = final_ideas
        st.success(ui_texts["final_idea_success"][lang_code])

    st.button(ui_texts["back_next_button"][lang_code], on_click=prev_page, key="back_from_final")
    st.button(ui_texts["next_back_button"][lang_code], on_click=next_page)
# 第 6 頁：體驗問卷 + 資料整合寫入
elif st.session_state.page == 6:
    # ✅ 完整的7分量表問卷
    questionnaire_data = {
        "title": {
            "E": "🎯 Research Questionnaire",
            "C": "🎯 研究問卷調查"
        },
        "scale_options": {
            "E": [
                "1: Strongly disagree",
                "2: Disagree", 
                "3: Slightly disagree",
                "4: Neutral",
                "5: Slightly agree",
                "6: Agree",
                "7: Strongly agree"
            ],
            "C": [
                "1: 非常不同意",
                "2: 不同意",
                "3: 有點不同意", 
                "4: 普通",
                "5: 有點同意",
                "6: 同意",
                "7: 非常同意"
            ]
        },
        "sections": {
            "E": {
                "demographics": {
                    "title": "Section 1: Demographics",
                    "questions": [
                        {
                            "text": "Gender:",
                            "type": "radio",
                            "options": ["Male", "Female", "Prefer not to say"],
                            "key": "gender"
                        },
                        {
                            "text": "Year of Study:",
                            "type": "radio", 
                            "options": ["2nd Year", "3rd Year", "4th Year", "Graduate"],
                            "key": "year_study"
                        },
                        {
                            "text": "Major:",
                            "type": "radio",
                            "options": ["College of Hospitality", "College of Tourism", "College of Culinary Arts", "College of International Studies", "Other"],
                            "key": "major"
                        },
                        {
                            "text": "Prior Experience with Generative AI:",
                            "type": "radio",
                            "options": ["Never used", "Novice", "Intermediate", "Advanced"],
                            "key": "ai_experience"
                        }
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
                        {
                            "text": "生理性別：",
                            "type": "radio",
                            "options": ["男", "女", "不願透露"],
                            "key": "gender"
                        },
                        {
                            "text": "年級：",
                            "type": "radio",
                            "options": ["大二", "大三", "大四", "研究所"],
                            "key": "year_study"
                        },
                        {
                            "text": "主修科系：",
                            "type": "radio",
                            "options": ["餐旅學院", "觀光學院", "廚藝學院", "國際學院", "其他"],
                            "key": "major"
                        },
                        {
                            "text": "生成式 AI (如 ChatGPT) 使用經驗：",
                            "type": "radio",
                            "options": ["從未用過", "初學者 (偶爾嘗試)", "中等程度 (曾用於作業或日常事務)", "進階使用者 (經常使用並熟悉提示詞技巧)"],
                            "key": "ai_experience"
                        }
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
                        "使用 小Q改善了我解決個案研究的表現。",
                        "這個 小Q讓我能比自己單獨作業時更快擬定問題。",
                        "我發現小Q對於產生「更多樣化」的問題很有用。",
                        "使用小Q讓我更容易理解核心問題所在。",
                        "整體而言，我覺得小Q對我的學習過程很有用。",
                        "我與 小Q的互動過程是清晰易懂的。",
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
                        "在 小Q的協助下，我能比平常提出更多的解決方案。",
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
    
    # Section 1: Demographics
    st.subheader(questionnaire_data["sections"][lang_code]["demographics"]["title"])
    for q_data in questionnaire_data["sections"][lang_code]["demographics"]["questions"]:
        responses[q_data["key"]] = st.radio(
            q_data["text"], 
            q_data["options"], 
            key=f"demo_{q_data['key']}"
        )
    
    # Section 2: Problem-Solving Style  
    st.subheader(questionnaire_data["sections"][lang_code]["problem_solving"]["title"])
    for i, question in enumerate(questionnaire_data["sections"][lang_code]["problem_solving"]["questions"]):
        selected_option = st.radio(
            question,
            scale_options,
            key=f"ps_{i+1}"
        )
        # 提取數字值用於資料儲存 (1-7)
        responses[f"problem_solving_{i+1}"] = int(selected_option.split(":")[0])
    
    # Section 3: AI Experience
    st.subheader(questionnaire_data["sections"][lang_code]["ai_experience_section"]["title"])
    for i, question in enumerate(questionnaire_data["sections"][lang_code]["ai_experience_section"]["questions"]):
        selected_option = st.radio(
            question,
            scale_options,
            key=f"ai_exp_{i+1}"
        )
        # 提取數字值用於資料儲存 (1-7)
        responses[f"ai_experience_{i+1}"] = int(selected_option.split(":")[0])
    
    # Section 5: Outcomes (Note: keeping as Section 5 as per original)
    st.subheader(questionnaire_data["sections"][lang_code]["outcomes"]["title"])
    for i, question in enumerate(questionnaire_data["sections"][lang_code]["outcomes"]["questions"]):
        selected_option = st.radio(
            question,
            scale_options,
            key=f"outcomes_{i+1}"
        )
        # 提取數字值用於資料儲存 (1-7)
        responses[f"outcomes_{i+1}"] = int(selected_option.split(":")[0])
    
    # Section 6: Future Outlook
    st.subheader(questionnaire_data["sections"][lang_code]["future"]["title"])
    for i, question in enumerate(questionnaire_data["sections"][lang_code]["future"]["questions"]):
        selected_option = st.radio(
            question,
            scale_options,
            key=f"future_{i+1}"
        )
        # 提取數字值用於資料儲存 (1-7)
        responses[f"future_{i+1}"] = int(selected_option.split(":")[0])

    if st.button(ui_texts["survey_submit"][lang_code], key="submit_survey_final"):
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
        gpt_interactions = [item for item in st.session_state.get("gpt_chat", []) if item[0] == "user"]
        for i, (role, text) in enumerate(gpt_interactions):
            final_row[f"GPT 問題{i+1}"] = text

        # ✅ 問卷結果 - 新的完整版本
        final_row.update(responses)

        # ✅ 寫入本地 Excel
        df = pd.concat([df, pd.DataFrame([final_row])], ignore_index=True)
        df.to_excel("Database.xlsx", index=False)
        st.success(ui_texts["survey_success"][lang_code])

        # ✅ 寫入 Google Sheet（失敗時提示）
        try:
            from google_sheet_sync import write_to_google_sheet
            write_to_google_sheet(final_row)
        except Exception as e:
            st.warning(ui_texts["survey_backup_warning"][lang_code].format(error=e))

# 第 7 頁：教師報表頁
elif st.session_state.page == 7:
    st.title(ui_texts["admin_title"][lang_code])

    PASSWORD = "!@#$123456"
    pw = st.text_input(ui_texts["admin_password_prompt"][lang_code], type="password", key="admin_pw")

    if pw != PASSWORD:
        st.warning(ui_texts["admin_password_warning"][lang_code])
        st.stop()

    st.success(ui_texts["admin_login_success"][lang_code])

    try:
        df = pd.read_excel("Database.xlsx")
    except:
        st.error(ui_texts["admin_no_data_error"][lang_code])
        st.stop()

    if df.empty:
        st.warning(ui_texts["admin_no_records"][lang_code])
    else:
        st.dataframe(df)

        # ✅ 提供 Excel 匯出
        st.download_button(ui_texts["admin_export_excel"][lang_code], data=open("Database.xlsx", "rb").read(), file_name="Database.xlsx")

        # ✅ 匯出 PDF
        from io import BytesIO
        from fpdf import FPDF
        from datetime import datetime

        if st.button(ui_texts["admin_export_pdf"][lang_code], key="dl_pdf"):
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
            st.download_button(ui_texts["admin_download_pdf"][lang_code], data=pdf_bytes, file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
