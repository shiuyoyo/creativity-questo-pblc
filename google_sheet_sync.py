import gspread
from oauth2client.service_account import ServiceAccountCredentials

def write_to_google_sheet(row_data: dict):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("creativity-records-app-43299a8269f4.json", scope)
        client = gspread.authorize(creds)

        # 👇 在這裡填入你的 Google Sheet 名稱
        sheet = client.open("Creativity Records").sheet1

        # 確保欄位順序一致
        existing_headers = sheet.row_values(1)
        if not existing_headers:
            sheet.insert_row(list(row_data.keys()), 1)
        row_values = [row_data.get(h, "") for h in sheet.row_values(1)]
        sheet.append_row(row_values)
        print("✅ Google Sheet 備份成功")
    except Exception as e:
        print("❌ 寫入 Google Sheet 失敗：", e)