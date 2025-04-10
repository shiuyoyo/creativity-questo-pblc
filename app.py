import streamlit as st
import pandas as pd
from datetime import datetime
from chat import LLM

st.set_page_config(page_title="Questo - Creativity Assistant", layout="centered")

# Initialize session state
if 'llm' not in st.session_state:
    st.session_state.llm = LLM()
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_id' not in st.session_state:
    st.session_state.user_id = f"User_{datetime.now().strftime('%H%M%S')}"

# Admin mode toggle
admin_mode = st.sidebar.checkbox("📊 教師後台報表 / Admin Dashboard")

if admin_mode:
    st.title("📊 教師後台報表")
    try:
        df = pd.read_excel("Database.xlsx")
        st.markdown("### 所有互動紀錄")
        st.dataframe(df)

        st.markdown("### 📈 問題類型統計")
        qtype_counts = df["問題類型"].value_counts().rename({"1": "指導性問題", "2": "創意問題"})
        st.bar_chart(qtype_counts)

        st.markdown("### 🧩 SCAMPER 類型分布")
        scamper_counts = df["SCAMPER 類型"].value_counts()
        st.bar_chart(scamper_counts)

        st.markdown("### ⏱️ 提問時間軸")
        df["時間戳記"] = pd.to_datetime(df["時間戳記"])
        df_sorted = df.sort_values("時間戳記")
        st.line_chart(df_sorted.groupby(df_sorted["時間戳記"].dt.floor('min')).size())
    except Exception as e:
        st.error(f"無法讀取 Excel 檔案：{e}")
else:
    # Language selection
    language = st.selectbox("Choose your language / 選擇語言", ["English", "中文"], index=0)
    lang_code = 'E' if language == 'English' else 'C'

    # Display challenge description
    if lang_code == 'E':
        st.title("Challenge")
        st.markdown('''You have joined a competition that aims at sourcing the best idea for a hotel located in a business district of an urban city to find good uses of the waste it produces. The hotel is situated next to a hospital, a convention center, and a major tourist attraction.  
**Guests include:** Business travelers, Convention Attendees, Friends and Families of Patients, Tourists  
You are required to propose three best ideas for the competition based on **old towels to be disposed of**.  
To win the competition, your ideas should:
- Help transform the waste at the hotel into something that delights the guests  
- Be creative  
**Important Notes:**  
You do not have to worry about the costs and resources required.  
You do not have to delight all types of guests.
''')
        activity_prompt = "What are three of the most creative ideas you can think of?"
        ai_intro = "Now you can use our AI Questioning Assistant 'Questo' to improve your questioning technique. Spend at least 5 minutes asking about how to reuse old hotel towels to delight guests. Questo will give you feedback on your questions, not answers."
        input_prompt = "Hi! I'm Questo, your friendly AI assistant. Ask me anything about reusing hotel towels creatively. Type 'end' to move on."
        post_prompt = "After chatting with ChatGPT, what are the three most creative ideas you came up with?"
        chatgpt_link_label = "Click here to chat with real ChatGPT"
    else:
        st.title("挑戰")
        st.markdown('''你要參加一個比賽，是在為一間位於都市商業區的飯店尋找最佳理念，找到飯店產生的廢棄物的良好用途。該飯店位於醫院、會議中心和主要旅遊景點旁邊。  
**其客群主要為：** 商務旅客、會議參加者、病人的親友、遊客  
你需要利用被處理的舊毛巾為比賽提出三個最佳理念。  
為了贏得比賽，你的理念應該：
- 幫助將酒店的廢棄物轉化為令客人愉悅的東西  
- 富有創意  
**注意事項：**  
你不必擔心實施的成本和資源。  
你不必取悅所有類型的客人。
''')
        activity_prompt = "要贏得比賽，您能想到的最具創意的三個想法是什麼？"
        ai_intro = "現在，你可以使用我們的人工智慧提問助手「小Q」來改善你的提問技巧，並產生更有效的問題。請花至少 5 分鐘的時間，提出與「如何利用舊飯店毛巾取悅顧客」相關的問題。小Q 不會提供答案，而是給你建議與回饋。"
        input_prompt = "嗨，你好！我是「小Q」，你友善的人工智慧提問小幫手。我來幫助你針對「如何將舊飯店毛巾變成讓顧客開心的東西」這個主題，創造出很棒的問題！(輸入「結束」就可以進入下一階段囉！)"
        post_prompt = "與 ChatGPT 聊天後，你能想到的最具創意的三個想法是什麼？"
        chatgpt_link_label = "點我開啟 ChatGPT 對話頁面"

    # Activity entry
    st.header(activity_prompt)
    activity = st.text_area("", value="")

    if st.button("Start"):
        st.session_state.llm.setup_language_and_activity(lang_code, activity)
        st.success("Activity and language set!")

    # AI guidance intro
    st.subheader("🧠 " + ai_intro)
    question = st.text_input(input_prompt)
    if st.button("送出問題 / Submit question"):
        llm_response = st.session_state.llm.Chat(question, lang_code, activity)
        st.session_state.chat_history.append((question, llm_response))

        qtype = llm_response['OUTPUT']['CLS']
        if qtype == '1':
            st.info("**AI Feedback (Guidance):**\n" + llm_response['OUTPUT']['GUIDE'])
        elif qtype == '2':
            st.info("**AI Feedback (Evaluation):**\n" + llm_response['OUTPUT']['EVAL'])
            st.success("**Suggested Better Question:**\n" + llm_response['OUTPUT']['NEWQ'])
        else:
            st.warning("The input does not seem to be a question. Please try again.")

        try:
            df = pd.read_excel("Database.xlsx")
        except:
            df = pd.DataFrame()

        new_row = {
            "時間戳記": datetime.now().isoformat(),
            "使用者編號": st.session_state.user_id,
            "語言": language,
            "原始問題": question,
            "問題類型": qtype,
            "AI 回饋": llm_response['OUTPUT']['GUIDE'] or llm_response['OUTPUT']['EVAL'],
            "改寫建議": llm_response['OUTPUT']['NEWQ'],
            "SCAMPER 類型": llm_response['MISC']['SCAMPER_ELEMENT'],
            "成本估算": llm_response['MISC']['cost_input'] + llm_response['MISC']['cost_output']
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_excel("Database.xlsx", index=False)
        st.success("✅ 資料已儲存到 Excel！")

    # ChatGPT phase
    st.subheader("🌟 " + ("To spark your imagination, ask ChatGPT some questions about the towel challenge." if lang_code == 'E' else "為了激發你的想像力，請先向 ChatGPT 提出一些關於飯店毛巾挑戰的問題。"))
    st.markdown(f"[{chatgpt_link_label}](https://chatgpt.com)")
    final_ideas = st.text_area(post_prompt)

    if st.button("送出創意想法 / Submit final ideas"):
        try:
            df = pd.read_excel("Database.xlsx")
        except:
            df = pd.DataFrame()

        final_row = {
            "時間戳記": datetime.now().isoformat(),
            "使用者編號": st.session_state.user_id,
            "語言": language,
            "創意發想結果": final_ideas
        }
        df = pd.concat([df, pd.DataFrame([final_row])], ignore_index=True)
        df.to_excel("Database.xlsx", index=False)
        st.success("🎉 最終創意點子已送出並儲存！")
