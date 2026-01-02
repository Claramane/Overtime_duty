import json
import os
from datetime import datetime
import calendar
import logging
from typing import Union

# --- 設定 ---
# HOLIDAY_FILE = 'holiday_2026.json' # 原始路徑
# HOLIDAY_FILE = 'data/holiday_2026.json' # 更新路徑
HOLIDAY_FILE = 'holiday_2026.json' # 僅使用文件名，將在初始化時計算完整路徑

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s')
logger = logging.getLogger(__name__)

# --- 輔助函數 ---
def _parse_date(date_str: str) -> Union[datetime, None]:
    """將 YYYYMMDD 字串解析為 datetime 物件。"""
    try:
        return datetime.strptime(date_str, "%Y%m%d")
    except (ValueError, TypeError):
        logger.warning(f"無法解析日期字串: {date_str}")
        return None

# --- HolidayService 類別 ---
class HolidayService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(HolidayService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, holiday_file=HOLIDAY_FILE):
        if self._initialized:
            return
        
        self.holiday_file = holiday_file
        self.holidays = {}
        self.special_days = {} # 新增：用於儲存特殊日期 (是否放假=3)
        self._load_holidays()
        self._initialized = True

    def _load_holidays(self):
        """從 JSON 檔案載入假日資料。"""
        logger.info(f"開始載入假日檔案: {self.holiday_file}")
        
        # 確定最終使用的檔案路徑
        final_path = None
        
        try:
            # 先正規化路徑（解析 .. 等符號）
            normalized_path = os.path.abspath(self.holiday_file)
            
            # 1. 檢查正規化後的路徑是否存在
            if os.path.exists(normalized_path):
                final_path = normalized_path
                logger.info(f"✓ 使用路徑: {final_path}")
            # 2. 如果原始路徑是絕對路徑但不存在
            elif os.path.isabs(self.holiday_file):
                logger.error(f"✗ 絕對路徑不存在: {self.holiday_file}")
                raise FileNotFoundError(f"找不到假日檔案: {self.holiday_file}")
            else:
                # 3. 如果是相對路徑，嘗試多個位置
                logger.debug(f"檔案路徑為相對路徑，開始搜尋...")
                
                # 3a. 嘗試相對於服務檔案的位置 (backend/data/)
                script_dir = os.path.dirname(__file__)
                base_dir = os.path.abspath(os.path.join(script_dir, '..', '..'))
                data_dir = os.path.join(base_dir, 'data')
                potential_path = os.path.join(data_dir, os.path.basename(self.holiday_file))
                logger.debug(f"嘗試路徑 1 (backend/data/): {potential_path}")
                
                if os.path.exists(potential_path):
                    final_path = potential_path
                    logger.info(f"✓ 在 backend/data/ 找到檔案: {final_path}")
                else:
                    # 3b. 嘗試相對於當前工作目錄
                    cwd_path = os.path.join(os.getcwd(), self.holiday_file)
                    logger.debug(f"嘗試路徑 2 (當前工作目錄): {cwd_path}")
                    
                    if os.path.exists(cwd_path):
                        final_path = cwd_path
                        logger.info(f"✓ 在當前工作目錄找到檔案: {final_path}")
                    else:
                        # 3c. 嘗試在 backend/data 相對於當前工作目錄
                        backend_data_path = os.path.join(os.getcwd(), 'backend', 'data', os.path.basename(self.holiday_file))
                        logger.debug(f"嘗試路徑 3 (./backend/data/): {backend_data_path}")
                        
                        if os.path.exists(backend_data_path):
                            final_path = backend_data_path
                            logger.info(f"✓ 在 ./backend/data/ 找到檔案: {final_path}")
                        else:
                            logger.error(f"✗ 在所有位置都找不到假日檔案: {self.holiday_file}")
                            logger.error(f"  已嘗試的路徑:")
                            logger.error(f"    0. {normalized_path}")
                            logger.error(f"    1. {potential_path}")
                            logger.error(f"    2. {cwd_path}")
                            logger.error(f"    3. {backend_data_path}")
                            raise FileNotFoundError(f"找不到假日檔案: {self.holiday_file}")
            
            # 更新為最終路徑
            self.holiday_file = final_path
            logger.info(f"=== 最終使用的假日檔案路徑: {self.holiday_file} ===")
            with open(self.holiday_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            count = 0
            special_count = 0
            for item in data:
                date_str = item.get("西元日期")
                is_holiday_val = item.get("是否放假")
                # 驗證日期格式
                if not date_str or not isinstance(date_str, str) or len(date_str) != 8:
                    logger.warning(f"跳過無效的日期格式記錄: {item}")
                    continue
                try:
                    int(date_str)
                except ValueError:
                    logger.warning(f"跳過非數字的日期字串記錄: {item}")
                    continue
                    
                # 處理是否放假值
                try:
                    is_holiday_int = int(is_holiday_val)
                    if is_holiday_int == 2: # 是否放假 = 2 表示假日
                        self.holidays[date_str] = True
                        count += 1
                    elif is_holiday_int == 3: # 是否放假 = 3 表示特殊日
                        self.special_days[date_str] = True # 存入 special_days
                        self.holidays[date_str] = True # 特殊日也視為假日計算工時
                        special_count += 1
                        count += 1
                    elif is_holiday_int in [0, 1]: # 0=工作日, 1=休息日 (非假日)
                        self.holidays[date_str] = False
                    else:
                         logger.warning(f"未知的 '是否放假' 值 ({is_holiday_val}) 在日期 {date_str}。將視為非假日。")
                         self.holidays[date_str] = False
                except (ValueError, TypeError):
                    logger.warning(f"無效的 '是否放假' 值 ({is_holiday_val}) 在日期 {date_str}。將視為非假日。")
                    self.holidays[date_str] = False
            
            logger.info(f"Loaded {count} holidays (including {special_count} special days treated as holidays) from {self.holiday_file}")

        except FileNotFoundError:
            # 這個錯誤應該在前面已經處理，但再次捕捉以防萬一
            logger.error(f"錯誤：處理過程中找不到假日檔案 {self.holiday_file}")
            self.holidays = {} # 確保是空的字典
            self.special_days = {}
        except json.JSONDecodeError:
            logger.error(f"錯誤：解析假日檔案 {self.holiday_file} 失敗。")
            self.holidays = {} 
            self.special_days = {}
        except Exception as e:
            logger.error(f"載入假日檔案時發生未預期錯誤: {e}", exc_info=True)
            self.holidays = {} 
            self.special_days = {}

    def is_holiday(self, date_str: str) -> bool:
        """檢查指定日期是否為假日 (包含特殊日)。"""
        if not isinstance(date_str, str) or len(date_str) != 8:
            logger.warning(f"傳遞給 is_holiday 的日期格式無效: {date_str}")
            return False
        return self.holidays.get(date_str, False) # 預設為 False

    def is_special_day(self, date_str: str) -> bool:
        """檢查指定日期是否為特殊日 (是否放假=3)。"""
        if not isinstance(date_str, str) or len(date_str) != 8:
             logger.warning(f"傳遞給 is_special_day 的日期格式無效: {date_str}")
             return False
        return self.special_days.get(date_str, False)

    def get_weekday(self, date_str: str) -> str:
        """獲取指定日期的星期幾 (中文)。"""
        date_obj = _parse_date(date_str)
        if date_obj:
            weekdays = ["一", "二", "三", "四", "五", "六", "日"]
            return weekdays[date_obj.weekday()]
        return "未知"

    def get_holiday(self, date):
        holiday = next((h for h in self.holidays if h['西元日期'] == date), None)
        if holiday:
            logger.debug(f"Found holiday for date {date}: {holiday['備註']}")
        else:
            logger.debug(f"No holiday found for date {date}")
        return holiday

    def update_holiday_status(self, date: str, status: int, description: str):
        logger.info(f"Updating holiday status for date {date}")
        for holiday in self.holidays:
            if holiday["西元日期"] == date:
                holiday["是否放假"] = str(status)
                holiday["備註"] = description
                break
        else:
            new_holiday = {
                "西元日期": date,
                "星期": datetime.strptime(date, "%Y%m%d").strftime("%a"),
                "是否放假": str(status),
                "備註": description
            }
            self.holidays.append(new_holiday)
            logger.info(f"Added new holiday: {new_holiday}")
        self.save_holidays()
        logger.info(f"Holiday status updated for date {date}")

    def get_special_days(self, year_month):
        special_days = [date for date in self._get_all_dates_in_month(year_month) if self.is_special_day(date)]
        logger.info(f"Found {len(special_days)} special days in {year_month}")
        return special_days

    def _get_all_dates_in_month(self, year_month):
        year = int(year_month[:4])
        month = int(year_month[4:])
        _, last_day = calendar.monthrange(year, month)
        dates = [f"{year_month}{day:02d}" for day in range(1, last_day + 1)]
        logger.debug(f"Generated {len(dates)} dates for {year_month}")
        return dates

    def get_holidays_in_month(self, year_month):
        holidays = [date for date in self._get_all_dates_in_month(year_month) if self.is_holiday(date)]
        logger.info(f"Found {len(holidays)} holidays in {year_month}")
        return holidays

    def get_holiday_info(self, date):
        holiday = self.get_holiday(date)
        if holiday:
            return {
                "date": holiday['西元日期'],
                "is_holiday": holiday['是否放假'] in ['2', '3'],
                "is_special": holiday['是否放假'] == '3',
                "description": holiday['備註']
            }
        else:
            return {
                "date": date,
                "is_holiday": False,
                "is_special": False,
                "description": ""
            }
        
    def get_month_info(self, year_month):
        all_dates = self._get_all_dates_in_month(year_month)
        month_info = [self.get_holiday_info(date) for date in all_dates]
        logger.info(f"Generated month info for {year_month}")
        return month_info

    def is_working_day(self, date):
        holiday = self.get_holiday(date)
        is_working = holiday is None or holiday['是否放假'] == '0'
        logger.debug(f"Is date {date} a working day? {is_working}")
        return is_working

    def get_working_days_in_month(self, year_month):
        working_days = [date for date in self._get_all_dates_in_month(year_month) if self.is_working_day(date)]
        logger.info(f"Found {len(working_days)} working days in {year_month}")
        return working_days

    def get_next_working_day(self, date):
        next_date = datetime.strptime(date, '%Y%m%d')
        while True:
            next_date += datetime.timedelta(days=1)
            if self.is_working_day(next_date.strftime('%Y%m%d')):
                logger.debug(f"Next working day after {date} is {next_date.strftime('%Y%m%d')}")
                return next_date.strftime('%Y%m%d')

    def get_previous_working_day(self, date):
        prev_date = datetime.strptime(date, '%Y%m%d')
        while True:
            prev_date -= datetime.timedelta(days=1)
            if self.is_working_day(prev_date.strftime('%Y%m%d')):
                logger.debug(f"Previous working day before {date} is {prev_date.strftime('%Y%m%d')}")
                return prev_date.strftime('%Y%m%d')

    def save_holidays(self):
        logger.info(f"Saving holidays to {self.holiday_file}")
        try:
            with open(self.holiday_file, 'w', encoding='utf-8') as f:
                json.dump(self.holidays, f, ensure_ascii=False, indent=4)
            logger.info("Holidays saved successfully")
        except Exception as e:
            logger.error(f"Error saving holidays: {str(e)}")