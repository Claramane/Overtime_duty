import logging
import os
import json
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import uvicorn
import re
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

# 匯入核心報表產生器
# 假設 api.main 在 src/api/ 目錄下
from ..core.report_generator import generate_reports

# 設定 Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s')
logger = logging.getLogger(__name__)

# 設定資料檔案路徑
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
HOLIDAY_FILE = os.path.join(DATA_DIR, 'holiday_2025.json')
DUTIES_FILE = os.path.join(DATA_DIR, 'duties.json')
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')

# 定義加班記錄模型
class DutyCreate(BaseModel):
    dateTime: str = Field(..., description="加班日期時間 (格式: YYYYMMDDHHMM)")
    hours: float = Field(..., description="加班時數")
    person: str = Field(..., description="加班人員名稱")
    reason: str = Field(..., description="加班原因")

class Duty(DutyCreate):
    id: str = Field(..., description="加班記錄唯一ID")

# 建立 FastAPI 應用程式實例
app = FastAPI(
    title="加班時數報表產生器 API",
    description="此 API 用於觸發產生醫師加班時數 Excel 報表。",
    version="1.0.0"
)

# 新增 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有來源，生產環境中應設定為特定域名
    allow_credentials=True,
    allow_methods=["*"],  # 允許所有 HTTP 方法
    allow_headers=["*"],  # 允許所有標頭
)

# --- 新增 API 端點 ---

# 獲取所有假日資料
@app.get("/holidays", summary="獲取所有假日資料")
async def get_all_holidays():
    try:
        with open(HOLIDAY_FILE, 'r', encoding='utf-8') as f:
            holidays = json.load(f)
        return holidays
    except Exception as e:
        logger.error(f"讀取假日資料時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail="無法讀取假日資料")

# 獲取特定月份的假日資料
@app.get("/holidays/month/{year_month}", summary="獲取特定月份的假日資料")
async def get_holidays_by_month(year_month: str):
    try:
        with open(HOLIDAY_FILE, 'r', encoding='utf-8') as f:
            all_holidays = json.load(f)
        
        month_holidays = [h for h in all_holidays if h["西元日期"].startswith(year_month)]
        return month_holidays
    except Exception as e:
        logger.error(f"讀取 {year_month} 月份假日資料時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"無法讀取 {year_month} 月份假日資料")

# 更新假日狀態
@app.put("/holidays/{date}", summary="更新假日狀態")
async def update_holiday_status(date: str, status: str, description: str = ""):
    try:
        with open(HOLIDAY_FILE, 'r', encoding='utf-8') as f:
            all_holidays = json.load(f)
        
        # 查找是否已存在該日期
        for holiday in all_holidays:
            if holiday["西元日期"] == date:
                holiday["是否放假"] = status
                holiday["備註"] = description
                break
        else:
            # 如果不存在，添加新記錄
            new_holiday = {
                "西元日期": date,
                "星期": "",  # 這裡需要計算星期幾，暫時留空
                "是否放假": status,
                "備註": description
            }
            all_holidays.append(new_holiday)
        
        with open(HOLIDAY_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_holidays, f, ensure_ascii=False, indent=4)
        
        return {"success": True, "message": f"成功更新 {date} 假日狀態"}
    except Exception as e:
        logger.error(f"更新假日狀態時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail="無法更新假日狀態")

# 獲取所有值班記錄
@app.get("/duties", summary="獲取所有值班記錄")
async def get_all_duties():
    try:
        with open(DUTIES_FILE, 'r', encoding='utf-8') as f:
            duties = json.load(f)
        return duties
    except Exception as e:
        logger.error(f"讀取值班記錄時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail="無法讀取值班記錄")

# 獲取特定月份的值班記錄
@app.get("/duties/month/{year_month}", summary="獲取特定月份的值班記錄")
async def get_duties_by_month(year_month: str):
    try:
        with open(DUTIES_FILE, 'r', encoding='utf-8') as f:
            all_duties = json.load(f)
        
        month_duties = [d for d in all_duties if d.get("dateTime", "").startswith(year_month)]
        return month_duties
    except Exception as e:
        logger.error(f"讀取 {year_month} 月份值班記錄時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"無法讀取 {year_month} 月份值班記錄")

# 獲取特定人員的值班記錄
@app.get("/duties/person/{person}", summary="獲取特定人員的值班記錄")
async def get_duties_by_person(person: str):
    try:
        with open(DUTIES_FILE, 'r', encoding='utf-8') as f:
            all_duties = json.load(f)
        
        person_duties = [d for d in all_duties if d.get("person") == person]
        return person_duties
    except Exception as e:
        logger.error(f"讀取 {person} 的值班記錄時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"無法讀取 {person} 的值班記錄")

# 新增加班記錄
@app.post("/duties", summary="新增加班記錄", response_model=Duty)
async def add_duty(duty_data: DutyCreate):
    try:
        # 讀取現有的加班記錄
        with open(DUTIES_FILE, 'r', encoding='utf-8') as f:
            all_duties = json.load(f)
        
        # 生成新記錄ID (使用遞增數字)
        max_id = 0
        for duty in all_duties:
            try:
                duty_id = int(duty.get("id", "0"))
                if duty_id > max_id:
                    max_id = duty_id
            except ValueError:
                continue
        
        # 建立新記錄
        new_duty = {
            "id": str(max_id + 1),
            "dateTime": duty_data.dateTime,
            "hours": duty_data.hours,
            "person": duty_data.person,
            "reason": duty_data.reason
        }
        
        # 添加到記錄列表
        all_duties.append(new_duty)
        
        # 保存到文件
        with open(DUTIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_duties, f, ensure_ascii=False, indent=4)
        
        logger.info(f"成功新增加班記錄: {new_duty}")
        return new_duty
    except Exception as e:
        logger.error(f"新增加班記錄時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"無法新增加班記錄: {str(e)}")

# 刪除加班記錄
@app.delete("/duties/{duty_id}", summary="刪除加班記錄")
async def delete_duty(duty_id: str):
    try:
        # 讀取現有的加班記錄
        with open(DUTIES_FILE, 'r', encoding='utf-8') as f:
            all_duties = json.load(f)
        
        # 尋找要刪除的記錄
        initial_count = len(all_duties)
        all_duties = [duty for duty in all_duties if duty.get("id") != duty_id]
        
        # 檢查是否有記錄被刪除
        if len(all_duties) == initial_count:
            logger.warning(f"未找到ID為 {duty_id} 的加班記錄")
            raise HTTPException(status_code=404, detail=f"未找到ID為 {duty_id} 的加班記錄")
        
        # 保存到文件
        with open(DUTIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_duties, f, ensure_ascii=False, indent=4)
        
        logger.info(f"成功刪除ID為 {duty_id} 的加班記錄")
        return {"success": True, "message": f"成功刪除ID為 {duty_id} 的加班記錄"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除加班記錄時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"無法刪除加班記錄: {str(e)}")

# 下載生成的 Excel 文件
@app.get("/download/{filename}", summary="下載生成的 Excel 文件")
async def download_file(filename: str):
    try:
        file_path = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"找不到文件: {filename}")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下載文件 {filename} 時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"無法下載文件: {filename}")

# --- 原有的報表生成端點 ---
@app.post("/generate_report/{year_month}", 
          summary="產生指定年月的加班報表",
          description="觸發指定年月 (格式 YYYYMM) 的報表產生流程。\n"
                      "可以選擇性地透過 `member_id` 參數指定單一成員。\n"
                      "成功後返回包含已產生檔案路徑的列表。")
async def trigger_report_generation(
    year_month: str, 
    member_id: Optional[str] = Query(None, description="要處理的特定成員 ID (例如: A, B)。如果省略，則處理所有成員。")
):
    """
    處理報表產生請求。

    Args:
        year_month (str): 目標年月 (路徑參數)，格式必須是 YYYYMM。
        member_id (Optional[str]): 目標成員 ID (查詢參數)。

    Returns:
        JSONResponse: 包含操作結果和已產生檔案列表的 JSON 回應。
    """
    logger.info(f"收到報表產生請求: 年月={year_month}, 成員ID={member_id}")

    # 驗證 year_month 格式
    if not re.match(r"^\d{6}$", year_month):
        logger.error(f"無效的 year_month 格式: {year_month}")
        raise HTTPException(status_code=400, detail="年月格式錯誤，請使用 YYYYMM 格式。")

    try:
        # 呼叫核心邏輯
        generated_files_info = generate_reports(year_month, member_id)
        
        if not generated_files_info:
            logger.warning(f"針對 {year_month} (成員: {member_id or '所有'}) 未產生任何報表檔案。")
            return JSONResponse(
                status_code=200, # 即使未產生檔案，請求本身也是成功的
                content={
                    "message": f"已完成處理 {year_month} (成員: {member_id or '所有'})，但未產生任何新的報表檔案。可能原因：該月份無值班記錄，或指定的成員 ID 不存在。",
                    "generated_files": []
                }
            )
        
        # 準備回應內容
        response_files = [{"path": path, "url": url} for path, url in generated_files_info]
        logger.info(f"成功產生 {len(response_files)} 個報表檔案。")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"成功產生 {year_month}  加班表。",
                "generated_files": response_files
            }
        )

    except FileNotFoundError as e:
         logger.error(f"處理請求時發生檔案找不到錯誤: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail=f"伺服器內部錯誤：缺少必要的設定檔 ({e})。")
    except Exception as e:
        logger.error(f"處理報表產生請求時發生未預期錯誤: {e}", exc_info=True)
        # 避免洩漏過多內部錯誤細節給客戶端
        raise HTTPException(status_code=500, detail=f"伺服器內部錯誤，無法完成報表產生。請檢查伺服器日誌。錯誤類型: {type(e).__name__}")

# --- 運行伺服器 ---
# 這個區塊允許你直接執行 `python src/api/main.py` 來啟動伺服器進行測試
# 但在生產環境中，建議使用 uvicorn 命令來啟動，例如：
# uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8088
if __name__ == "__main__":
    logger.info("直接啟動 API 伺服器 (用於測試)...")
    # 注意：直接運行時，uvicorn 的 reload 可能不會如預期般工作
    # 建議使用 uvicorn 命令啟動
    uvicorn.run(app, host="127.0.0.1", port=8088, log_level="info") 