# 後端需要添加以下代碼（Python, FastAPI格式）

```python
@app.get("/duties/month/{year_month}")
async def get_duties_for_month(year_month: str):
    """
    根據年月獲取加班記錄
    
    Args:
        year_month (str): 年月字符串，格式為YYYYMM
        
    Returns:
        List[Duty]: 符合指定年月的加班記錄列表
    """
    try:
        # 從JSON文件讀取所有值班記錄
        with open("data/duties.json", "r", encoding="utf-8") as f:
            all_duties = json.load(f)
        
        # 過濾出指定年月的記錄
        filtered_duties = [duty for duty in all_duties if duty["dateTime"].startswith(year_month)]
        
        return filtered_duties
    except Exception as e:
        logger.error(f"獲取{year_month}加班記錄失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取加班記錄失敗: {str(e)}")
```

# 後端修改 `/generate_report/{year_month}` 端點的建議

```python
@app.post("/generate_report/{year_month}")
async def generate_report(year_month: str, member_id: Optional[str] = None):
    """
    產生並下載指定年月的加班報表
    
    Args:
        year_month (str): 年月字符串，格式為YYYYMM
        member_id (str, optional): 成員ID，如果提供則只生成該成員的報表
        
    Returns:
        StreamingResponse: 直接返回ZIP文件流供下載
    """
    try:
        # 產生報表的邏輯
        # ...略...
        
        # 創建報表文件
        file_path = f"data/output/overtime_report_{year_month}.xlsx"
        
        # 將文件打包成ZIP
        zip_path = f"data/output/overtime_report_{year_month}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(file_path, os.path.basename(file_path))
        
        # 返回文件流
        return StreamingResponse(
            open(zip_path, "rb"),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=overtime_report_{year_month}.zip"
            }
        )
    except Exception as e:
        logger.error(f"產生報表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"產生報表失敗: {str(e)}")
``` 