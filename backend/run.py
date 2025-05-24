import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",  # 允許外部訪問
        port=8088,
        reload=True,
        log_level="info"
    ) 