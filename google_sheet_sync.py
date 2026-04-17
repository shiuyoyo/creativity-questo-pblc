import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials


def write_to_google_sheet(row_data: dict):
    try:
        required_keys = [
            "gcp_project_id",
            "gcp_private_key_id",
            "gcp_private_key",
            "gcp_client_email",
            "gcp_client_id",
            "gcp_client_x509_cert_url",
        ]

        missing_keys = [key for key in required_keys if key not in st.secrets]
        if missing_keys:
            print(f"❌ 缺少 Streamlit secrets: {missing_keys}")
            return False

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

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

        headers = sheet.row_values(1)
        if not headers:
            headers = list(row_data.keys())
            sheet.insert_row(headers, 1)

        row_values = [row_data.get(header, "") for header in headers]
        sheet.append_row(row_values)

        print("✅ Google Sheet 備份成功")
        return True

    except Exception as e:
        print("❌ 寫入 Google Sheet 失敗：", e)
        return False
