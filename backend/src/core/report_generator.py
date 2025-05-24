import os
import json
import logging
import time
import argparse
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Optional

# 使用相對路徑匯入服務
from ..services.holiday_service import HolidayService
from ..services.excel_service import ExcelService

# 設定檔和金鑰的路徑 (相對於專案根目錄)
script_dir = os.path.dirname(__file__)
BASE_DIR = os.path.abspath(os.path.join(script_dir, '..', '..')) # 專案根目錄
DATA_DIR = os.path.join(BASE_DIR, 'data')
MEMBERS_FILE = os.path.join(DATA_DIR, 'members.json')
DUTIES_FILE = os.path.join(DATA_DIR, 'duties.json')
SERVICE_ACCOUNT_FILE = os.path.join(DATA_DIR, 'service_account.json')
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# 確保輸出目錄存在
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 確認檔案路徑
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s')
logger = logging.getLogger(__name__)
logger.info(f"BASE_DIR: {BASE_DIR}")
logger.info(f"DATA_DIR: {DATA_DIR}")
logger.info(f"MEMBERS_FILE: {MEMBERS_FILE}")
logger.info(f"DUTIES_FILE: {DUTIES_FILE}")
logger.info(f"SERVICE_ACCOUNT_FILE: {SERVICE_ACCOUNT_FILE}")
logger.info(f"OUTPUT_DIR: {OUTPUT_DIR}")

def load_members():
    """從 data/members.json 載入成員資料。"""
    try:
        with open(MEMBERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        members = {member['id']: member for member in data.get('calendars', [])}
        logger.info(f"成功從 {MEMBERS_FILE} 載入 {len(members)} 位成員資料。")
        return members
    except FileNotFoundError:
        logger.error(f"錯誤：找不到成員檔案 {MEMBERS_FILE}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"錯誤：解析成員檔案 {MEMBERS_FILE} 失敗。")
        return {}
    except Exception as e:
        logger.error(f"載入成員檔案時發生未預期錯誤: {e}", exc_info=True)
        return {}

def get_credentials():
    """使用 data/service_account.json 獲取憑證。"""
    try:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            logger.error(f"錯誤：找不到服務帳號金鑰檔案 {SERVICE_ACCOUNT_FILE}。")
            raise FileNotFoundError(f"找不到 {SERVICE_ACCOUNT_FILE}")
        
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        logger.info(f"成功從 {SERVICE_ACCOUNT_FILE} 載入服務帳號憑證。")
        return creds
    except Exception as e:
        logger.error(f"從服務帳號檔案載入憑證時發生錯誤: {e}", exc_info=True)
        raise

def _add_hours_to_time(date: str, time_str: str, hours: float) -> dict:
    """將小時數添加到日期時間。"""
    logger.debug(f"Adding {hours} hours to {date} {time_str}")
    try:
        datetime_obj = datetime.strptime(f"{date}{time_str}", "%Y%m%d%H%M")
        new_datetime = datetime_obj + timedelta(hours=hours)
        return {
            "date": new_datetime.strftime("%Y%m%d"),
            "time": new_datetime.strftime("%H%M")
        }
    except Exception as e:
        logger.error(f"Error in _add_hours_to_time for {date} {time_str} + {hours}h: {e}", exc_info=True)
        raise

def _calculate_hours_between(start_time: str, end_time: str) -> float:
    """計算兩個時間點之間的小時數。"""
    try:
        start = datetime.strptime(start_time, "%H%M")
        end = datetime.strptime(end_time, "%H%M")
        if end < start:
            end += timedelta(days=1)
        diff = end - start
        hours = diff.total_seconds() / 3600
        return round(hours * 2) / 2
    except Exception as e:
        logger.error(f"Error in _calculate_hours_between for {start_time}-{end_time}: {e}", exc_info=True)
        return 0.0

def _load_manual_duties(year_month: str, member_info: dict) -> list[dict]:
    """從 data/duties.json 載入指定年月和成員的手動值班記錄。"""
    logger.info(f"Loading manual duties for {year_month} and member {member_info['name']}")
    manual_duties = []
    if not os.path.exists(DUTIES_FILE):
        logger.warning(f"Manual duties file not found: {DUTIES_FILE}. Skipping manual duties.")
        return []

    try:
        with open(DUTIES_FILE, 'r', encoding='utf-8') as f:
            all_manual_duties_data = json.load(f)
        logger.debug(f"Loaded {len(all_manual_duties_data)} raw duties from {DUTIES_FILE}")

        for duty_entry in all_manual_duties_data:
            if duty_entry.get('dateTime', '').startswith(year_month) and duty_entry.get('person') == member_info['name']:
                try:
                    date_str = duty_entry['dateTime'][:8]
                    start_time_str = duty_entry['dateTime'][8:]
                    hours = float(duty_entry['hours'])
                    reason = duty_entry.get('reason', 'N/A')
                    datetime.strptime(start_time_str, "%H%M") # Validate format

                    end_time_info = _add_hours_to_time(date_str, start_time_str, hours)
                    end_date_str = end_time_info['date']
                    end_time_str = end_time_info['time']

                    base_manual_shift = {
                        "start": start_time_str,
                        "end": end_time_str,
                        "is_manual": True,
                        "reason": reason,
                        "original_hours": hours
                    }

                    if end_date_str == date_str:
                        manual_shift = base_manual_shift.copy()
                        manual_shift["date"] = date_str
                        manual_duties.append(manual_shift)
                        logger.debug(f"Added non-crossing manual duty: {manual_shift}")
                    else:
                        first_day_end = "2400"
                        first_day_shift = base_manual_shift.copy()
                        first_day_shift["date"] = date_str
                        first_day_shift["end"] = first_day_end
                        manual_duties.append(first_day_shift)
                        logger.debug(f"Added crossing manual duty (Part 1): {first_day_shift}")

                        second_day_start = "0000"
                        second_day_shift = base_manual_shift.copy()
                        second_day_shift["date"] = end_date_str
                        second_day_shift["start"] = second_day_start
                        manual_duties.append(second_day_shift)
                        logger.debug(f"Added crossing manual duty (Part 2): {second_day_shift}")

                except ValueError as ve:
                    logger.warning(f"Skipping manual duty due to invalid format in dateTime ({duty_entry.get('dateTime')}) or hours ({duty_entry.get('hours')}): {ve} - Entry: {duty_entry}")
                except KeyError as ke:
                    logger.warning(f"Skipping manual duty due to missing key {ke}. Entry: {duty_entry}")
                except Exception as e:
                    logger.error(f"Error processing manual duty entry {duty_entry}: {e}", exc_info=True)

    except FileNotFoundError:
        logger.warning(f"Manual duties file not found: {DUTIES_FILE}")
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from manual duties file: {DUTIES_FILE}")
    except Exception as e:
        logger.error(f"Error loading or processing manual duties from {DUTIES_FILE}: {e}", exc_info=True)

    logger.info(f"Loaded {len(manual_duties)} manual duty segments for {year_month} and member {member_info['name']}")
    return manual_duties

def _calculate_shift_hours(holiday_service: HolidayService, date_str: str, start_time: str, end_time: str) -> list[float]:
    """根據日期、時間和假日資訊計算工時分類。"""
    is_holiday = holiday_service.is_holiday(date_str)
    is_special = holiday_service.is_special_day(date_str)
    logger.debug(f"Calculating work hours - date: {date_str}, start: {start_time}, end: {end_time}, is_holiday/special: {is_holiday or is_special}")
    
    try:
        start = datetime.strptime(f"{date_str}{start_time}", "%Y%m%d%H%M")
        if end_time == "2400":
            end_date_obj = datetime.strptime(date_str, "%Y%m%d") + timedelta(days=1)
            end = datetime.strptime(f"{end_date_obj.strftime('%Y%m%d')}0000", "%Y%m%d%H%M")
        else:
            end_date_str_for_end = date_str
            if datetime.strptime(end_time, "%H%M") < datetime.strptime(start_time, "%H%M"):
                 end_date_obj = datetime.strptime(date_str, "%Y%m%d") + timedelta(days=1)
                 end_date_str_for_end = end_date_obj.strftime("%Y%m%d")
            end = datetime.strptime(f"{end_date_str_for_end}{end_time}", "%Y%m%d%H%M")
        
        if end < start:
             logger.warning(f"End time {end} is before start time {start} after date adjustment. Re-adjusting end date.")
             end += timedelta(days=1)

        total_hours = (end - start).total_seconds() / 3600
        total_hours = round(total_hours * 2) / 2
        logger.debug(f"Calculated total hours: {total_hours}")
        
        if is_holiday or is_special:
            hours_h = min(8, total_hours)
            hours_i = max(0, total_hours - 8)
            result = [0.0, 0.0, 0.0, hours_h, hours_i]
        else:
            hours_e = min(2, total_hours)
            hours_f = min(2, max(0, total_hours - 2))
            hours_g = max(0, total_hours - 4)
            result = [hours_e, hours_f, hours_g, 0.0, 0.0]
        
        result = [round(float(x) * 2) / 2 for x in result]
        logger.debug(f"Calculated work hours result: {result}")
        return result
    except ValueError as ve:
        logger.error(f"Error parsing date/time in _calculate_shift_hours for {date_str} {start_time}-{end_time}: {ve}", exc_info=True)
        return [0.0] * 5
    except Exception as e:
        logger.error(f"Error in _calculate_shift_hours for {date_str} {start_time}-{end_time}: {str(e)}", exc_info=True)
        return [0.0] * 5

def get_events_in_range(service, calendar_id, time_min_iso, time_max_iso, member_name):
    """同步獲取指定日曆和日期範圍內的事件。"""
    try:
        logger.info(f"正在為 [{member_name}] ({calendar_id}) 獲取 {time_min_iso} 到 {time_max_iso} 的事件...")
        events_result = service.events().list(
            calendarId=calendar_id, timeMin=time_min_iso, timeMax=time_max_iso,
            singleEvents=True, orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        logger.info(f"成功為 [{member_name}] 在指定範圍內獲取 {len(events)} 個事件。")
        return events
    except HttpError as error:
        logger.error(f"為 [{member_name}] ({calendar_id}) 獲取事件時發生 HttpError ({error.resp.status}): {error.content.decode() if error.content else 'No content'}")
        if error.resp.status == 404:
            logger.warning(f"[{member_name}] - 日曆 ID 可能無效或無權限訪問: {calendar_id}")
        elif error.resp.status == 403:
             logger.warning(f"[{member_name}] - 權限不足 (Forbidden)，請檢查服務帳號是否已共享日曆並具有讀取權限: {calendar_id}")
        return []
    except Exception as e:
        logger.error(f"為 [{member_name}] ({calendar_id}) 獲取事件時發生未預期錯誤: {e}", exc_info=True)
        return []

def generate_reports(year_month: str, target_member_id: Optional[str] = None):
    """產生指定年月和成員 (可選) 的值班報表。

    Args:
        year_month (str): 目標年月 (YYYYMM)。
        target_member_id (Optional[str]): 目標成員 ID。如果為 None，則處理所有成員。

    Returns:
        list[tuple[str, str]]: 包含成功產生的 (檔案路徑, 相對 URL) 的列表。
    """
    generated_files = [] # 儲存成功產生的檔案路徑和 URL
    try:
        year = int(year_month[:4])
        month = int(year_month[4:])
        start_of_month = datetime(year, month, 1)
        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year += 1
        next_month_first_day = datetime(next_year, next_month, 1)

        time_min_iso = start_of_month.isoformat() + 'Z'
        time_max_dt_for_query = next_month_first_day + timedelta(hours=9)
        time_max_iso = time_max_dt_for_query.isoformat() + 'Z'

    except ValueError:
        logger.error(f"錯誤：年月格式不正確 ({year_month})，請使用 YYYYMM 格式。")
        return []

    # --- 初始化服務 ---
    try:
        # 明確傳遞絕對路徑以避免歧義
        holiday_service = HolidayService(holiday_file=os.path.join(DATA_DIR, 'holiday_2025.json'))
        excel_service = ExcelService(
            template_path=os.path.join(DATA_DIR, 'VSduty_template.xlsx'),
            output_dir=OUTPUT_DIR # 使用全局定義的 OUTPUT_DIR
        )
        logger.info(f"服務初始化完成，使用假日檔案: {os.path.join(DATA_DIR, 'holiday_2025.json')}")
        logger.info(f"服務初始化完成，使用模板檔案: {os.path.join(DATA_DIR, 'VSduty_template.xlsx')}")
        logger.info(f"服務初始化完成，使用輸出目錄: {OUTPUT_DIR}")
    except Exception as e:
        logger.critical(f"初始化服務時發生錯誤: {e}", exc_info=True)
        return []

    # --- 載入和過濾成員 ---
    all_members = load_members()
    if not all_members:
        return []
    logger.info(f"載入 {len(all_members)} 位成員設定: {list(all_members.keys())}") # 新增日誌

    members_to_fetch = {}
    if target_member_id:
        member_id_upper = target_member_id.upper()
        if member_id_upper in all_members:
            members_to_fetch = {member_id_upper: all_members[member_id_upper]}
            logger.info(f"準備為成員 ID [{member_id_upper}] 處理 {year_month}...")
        else:
            logger.error(f"錯誤：在 {MEMBERS_FILE} 中找不到指定的成員 ID [{member_id_upper}]。可用 ID: {list(all_members.keys())}")
            return []
    else:
        members_to_fetch = all_members
        logger.info(f"準備處理所有成員在 {year_month} 的資料...")
    
    if not members_to_fetch:
        logger.warning("沒有需要處理的成員。")
        return []

    # --- 建立 Google Calendar 服務 ---
    try:
        creds = get_credentials()
        google_service = build('calendar', 'v3', credentials=creds)
        logger.info("Google Calendar API 服務建立成功 (使用服務帳號)。")
    except Exception as e:
        logger.error(f"建立 Google Calendar 服務時發生錯誤: {e}", exc_info=True)
        return []

    # --- 開始處理和計時 ---
    start_process_time = time.time()
    total_members_processed = 0
    total_excel_generated = 0
    
    logger.info(f"開始順序處理 {len(members_to_fetch)} 個成員...")

    # --- 主迴圈：處理每個成員 ---
    for member_id, member_info in members_to_fetch.items():
        member_name = member_info.get('name', '未知姓名')
        calendar_id = member_info.get('calendar_id')
        
        if not calendar_id:
            logger.warning(f"成員 {member_name} ({member_id}) 缺少 calendar_id，已跳過。")
            continue

        logger.info(f"--- 開始處理成員: {member_name} ({member_id}) ---")
        
        # 1. 獲取 Google Calendar 事件
        google_events = get_events_in_range(google_service, calendar_id, time_min_iso, time_max_iso, member_name)
        logger.info(f"成員 [{member_name}] 從 Google Calendar 獲取到 {len(google_events) if google_events else 0} 個事件。") # 新增日誌
        
        if google_events is None: # 理論上 get_events_in_range 不會回 None，而是 []
             logger.error(f"獲取成員 [{member_name}] 的事件時返回 None，跳過處理。")
             continue

        # 2. 載入該成員的手動 Duty
        manual_duties = _load_manual_duties(year_month, member_info)
        logger.info(f"成員 [{member_name}] 從 duties.json 載入 {len(manual_duties)} 個手動班次段。") # 新增日誌

        # 3. 合併處理 Google Events 和 Manual Duties
        combined_shifts_by_date = {} 
        processed_calendar_duty_starts = set()

        # --- 3a. 處理 Google Events 轉換為標準班次 ---
        for event in google_events:
            try:
                start_info = event.get('start', {})
                start_date_str = None
                if 'dateTime' in start_info:
                    start_date_time_obj = datetime.fromisoformat(start_info['dateTime'])
                    start_date_str = start_date_time_obj.strftime('%Y%m%d')
                elif 'date' in start_info:
                    start_date_str = start_info['date'].replace('-', '')
                else:
                    logger.warning(f"事件缺少有效的 start date/dateTime: {event.get('summary', 'No Summary')}")
                    continue

                if not start_date_str.startswith(year_month):
                     logger.debug(f"Skipping event starting outside target month {year_month}: {start_date_str} - {event.get('summary', 'No Summary')}")
                     continue

                if start_date_str in processed_calendar_duty_starts:
                    logger.debug(f"Skipping duplicate standard duty trigger for date {start_date_str}: {event.get('summary', 'No Summary')}")
                    continue
                processed_calendar_duty_starts.add(start_date_str)

                is_holiday = holiday_service.is_holiday(start_date_str)
                standard_shifts = []
                next_day_obj = datetime.strptime(start_date_str, "%Y%m%d") + timedelta(days=1)
                next_day_str = next_day_obj.strftime("%Y%m%d")

                if is_holiday:
                    standard_shifts.append({'date': start_date_str, 'start': "0800", 'end': "2400", 'is_manual': False, 'reason': "10"})
                    standard_shifts.append({'date': next_day_str, 'start': "0000", 'end': "0800", 'is_manual': False, 'reason': "10"})
                else:
                    standard_shifts.append({'date': start_date_str, 'start': "1600", 'end': "2400", 'is_manual': False, 'reason': "10"})
                    standard_shifts.append({'date': next_day_str, 'start': "0000", 'end': "0800", 'is_manual': False, 'reason': "10"})

                for shift in standard_shifts:
                    date_key = shift['date']
                    if date_key not in combined_shifts_by_date:
                        combined_shifts_by_date[date_key] = []
                    combined_shifts_by_date[date_key].append(shift)
                    logger.debug(f"Added standard shift from calendar event: {shift}")

            except Exception as e:
                 logger.error(f"處理事件時發生錯誤 ({event.get('summary', 'No Summary')} on {start_date_str}): {e}", exc_info=True)

        # --- 3b. 合併手動 Duties ---
        for manual_shift in manual_duties:
             date_key = manual_shift['date']
             if date_key not in combined_shifts_by_date:
                 combined_shifts_by_date[date_key] = []
             combined_shifts_by_date[date_key].append(manual_shift)
             logger.debug(f"Added manual shift: {manual_shift}")

        # 4. 計算所有班次的工時並格式化為 Excel Duty 列表
        duties_for_excel = []
        for date_key, shifts_on_date in combined_shifts_by_date.items():
            if not date_key.startswith(year_month):
                logger.debug(f"Skipping shifts for date {date_key} as it's outside target month {year_month}.")
                continue

            for shift in shifts_on_date:
                try:
                    shift_date = shift['date']
                    shift_start = shift['start']
                    shift_end = shift['end']
                    is_manual = shift.get('is_manual', False)
                    reason = shift.get('reason', 'N/A')

                    weekday = holiday_service.get_weekday(shift_date)
                    work_hours = _calculate_shift_hours(holiday_service, shift_date, shift_start, shift_end)

                    duty = {
                        'date': shift_date,
                        'weekday': weekday,
                        'start': shift_start,
                        'end': shift_end,
                        'work_hours': work_hours,
                        'reason': reason,
                        'is_manual': is_manual
                    }
                    duties_for_excel.append(duty)
                    logger.debug(f"Prepared duty for Excel: {duty}")

                except KeyError as ke:
                     logger.warning(f"Skipping shift due to missing key {ke} during final processing: {shift}.")
                except Exception as e:
                    logger.error(f"Error processing combined shift {shift} for Excel: {e}", exc_info=True)

        logger.info(f"成員 [{member_name}] 準備寫入 Excel 的總記錄數: {len(duties_for_excel)}") # 新增日誌

        # 5. 排序最終 Duty 列表
        duties_for_excel.sort(key=lambda x: (x['date'], x['start']))
        
        # 6. 產生 Excel 檔案
        if duties_for_excel:
            try:
                logger.info(f"準備為 [{member_name}] 產生包含 {len(duties_for_excel)} 筆記錄 (含手動) 的 Excel 檔案...")
                if 'employee_id' not in member_info:
                     logger.error(f"成員 [{member_name}] 缺少 'employee_id'，無法產生 Excel。")
                else:
                    file_path, relative_url = excel_service.generate_excel(member_info, duties_for_excel, year_month)
                    if file_path and relative_url:
                        logger.info(f"成功為 [{member_name}] 產生 Excel: {file_path} (URL: {relative_url})")
                        generated_files.append((file_path, relative_url))
                        total_excel_generated += 1
                    else:
                         logger.error(f"為 [{member_name}] 產生 Excel 時 excel_service 返回 None")
            except Exception as e:
                logger.error(f"為 [{member_name}] 產生 Excel 時發生錯誤: {e}", exc_info=True)
        else:
            logger.info(f"成員 [{member_name}] 在 {year_month} 沒有從行事曆或手動記錄解析出任何有效值班記錄，不產生 Excel。")

        total_members_processed += 1
        logger.info(f"--- 完成處理成員: {member_name} ({member_id}) ---")

    # --- 計時結束和總結 --- 
    end_process_time = time.time()
    total_duration = end_process_time - start_process_time
    logger.info(f"=== {year_month} 報表產生完成 ({'Member ' + target_member_id if target_member_id else 'All Members'}) ===")
    logger.info(f"總共處理成員數: {total_members_processed}")
    logger.info(f"成功產生 Excel 檔案數: {total_excel_generated}")
    logger.info(f"總耗時: {total_duration:.2f} 秒。")
    
    return generated_files

# --- 主程式執行區塊 (用於直接執行此腳本進行測試或獨立運行) ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='從 Google Calendar 和 duties.json 獲取成員事件並產生 Excel 值班表。')
    parser.add_argument('--member-id', type=str, help='只處理特定成員 ID (例如: A, B, ...)')
    parser.add_argument('--year-month', type=str, default=datetime.now().strftime('%Y%m'), help='指定處理的年月 (格式 YYYYMM)，預設為當前年月')
    args = parser.parse_args()

    # 注意：直接執行時，相對路徑是相對於 core 目錄，需要調整
    # 這裡假設直接執行只是為了測試，路徑應能正確找到 data 目錄
    # 如果要打包或部署，應依賴上面的 BASE_DIR 和 DATA_DIR
    print(f"Executing report generation for {args.year_month}, Member: {args.member_id}")
    results = generate_reports(args.year_month, args.member_id)
    print("\n--- Generation Results ---")
    if results:
        for path, url in results:
            print(f"- Generated: {path} (URL: {url})")
    else:
        print("No reports were generated or an error occurred.")
    print("-------------------------") 