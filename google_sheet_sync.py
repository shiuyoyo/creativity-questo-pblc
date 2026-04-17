import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials


def column_letter(n: int) -> str:
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result


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

        # 這裡改成你的 Google Sheet 名稱
        sheet = client.open("Creativity Records New").sheet1

        expected_headers = list(row_data.keys())
        existing_headers = sheet.row_values(1)

        if not existing_headers:
            sheet.insert_row(expected_headers, 1)
            existing_headers = expected_headers
            print("✅ 已建立 Google Sheet 表頭")

        if existing_headers != expected_headers:
            end_col = column_letter(len(expected_headers))
            sheet.update(
                range_name=f"A1:{end_col}1",
                values=[expected_headers]
            )
            existing_headers = expected_headers
            print("⚠️ Google Sheet 表頭已自動校正")

        row_values = [row_data.get(header, "") for header in existing_headers]
        sheet.append_row(row_values)

        print("✅ Google Sheet 備份成功")
        return True

    except Exception as e:
        print("❌ 寫入 Google Sheet 失敗：", e)
        return False
