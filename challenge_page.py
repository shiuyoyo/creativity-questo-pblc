import streamlit as st

def show_challenge_page(lang_code, next_page_callback):
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
