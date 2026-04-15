import gspread
import json
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

def write_to_google_sheet(row_data: dict):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

        creds_dict = json.loads(st.secrets["gcp_json"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        sheet = client.open("Creativity Records").sheet1

        existing_headers = sheet.row_values(1)
        if not existing_headers:
            sheet.insert_row(list(row_data.keys()), 1)

        row_values = [row_data.get(h, "") for h in sheet.row_values(1)]
        sheet.append_row(row_values)
        print("✅ Google Sheet 備份成功")

    except Exception as e:
        print("❌ 寫入 Google Sheet 失敗：", e)
        raise
