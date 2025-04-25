import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="📊 教師報表下載頁", layout="centered")

PASSWORD = "!@#$123456"

# 密碼輸入
st.title("🔒 教師後台報表")
pw = st.text_input("請輸入教師密碼以檢視報表", type="password")

if pw != PASSWORD:
    st.warning("請輸入正確密碼以進入教師頁面")
    st.stop()

st.success("登入成功 ✅ 歡迎使用教師報表頁！")

# 讀取資料
try:
    df = pd.read_excel("Database.xlsx")
    st.dataframe(df)
except:
    st.error("⚠️ 無法讀取資料，請確認是否有正確的 Database.xlsx")
    st.stop()

# 建立 PDF
if st.button("📄 下載整合報表（PDF）"):
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
                value = str(row.get(col, "")).replace("\n", "
")
                pdf.multi_cell(0, 6, f"{col}: {value}")
        pdf.ln(5)

    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(f"/mnt/data/{filename}")
    st.success(f"✅ PDF 已建立：{filename}")
    st.download_button("📥 點我下載 PDF", data=open(f"/mnt/data/{filename}", "rb").read(), file_name=filename)