import gspread
import json
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

def write_to_google_sheet(row_data: dict):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

        creds_dict = {
            "type": "service_account",
            "project_id": st.secrets["gcp_project_id"],
            "private_key_id": st.secrets["gcp_private_key_id"],
            "private_key": st.secrets["gcp_private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["gcp_client_email"],
            "client_id": st.secrets["gcp_client_id"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": st.secrets["gcp_client_x509_cert_url"],
        }

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
