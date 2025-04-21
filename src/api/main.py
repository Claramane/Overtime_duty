import logging
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn
import re

# 匯入核心報表產生器
# 假設 api.main 在 src/api/ 目錄下
from ..core.report_generator import generate_reports

# 設定 Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s')
logger = logging.getLogger(__name__)

# 建立 FastAPI 應用程式實例
app = FastAPI(
    title="加班時數報表產生器 API",
    description="此 API 用於觸發產生醫師加班時數 Excel 報表。",
    version="1.0.0"
)

# --- API 端點 ---
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
                "message": f"成功為 {year_month} (成員: {member_id or '所有'}) 產生報表。",
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