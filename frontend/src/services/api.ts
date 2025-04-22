import axios from 'axios';
import { Holiday, Duty, ReportGenerationResponse, DutyCreate } from '../types';

// 直接使用相對路徑，讓Nginx處理代理
const API_BASE = '/api';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;

// API基礎URL設定
const API_URL_FULL = process.env.REACT_APP_API_URL || 'http://localhost:8088';

// 假日相關API
export const holidayApi = {
  // 獲取假日資料
  getHolidays: async (): Promise<Holiday[]> => {
    const response = await axios.get(`${API_BASE}/holidays`);
    return response.data;
  },

  // 獲取指定月份的假日資料
  getHolidaysForMonth: async (yearMonth: string): Promise<Holiday[]> => {
    const response = await axios.get(`${API_BASE}/holidays/month/${yearMonth}`);
    return response.data;
  },
  
  // 更新假日狀態
  updateHolidayStatus: async (date: string, status: number, description: string = ''): Promise<Holiday> => {
    const response = await axios.put(`${API_BASE}/holidays/${date}`, null, {
      params: { status: status.toString(), description }
    });
    return response.data;
  }
};

// 值班相關API
export const dutyApi = {
  // 獲取所有值班記錄
  getAllDuties: async (): Promise<Duty[]> => {
    const response = await axios.get(`${API_BASE}/duties`);
    return response.data;
  },

  // 獲取指定月份的值班記錄
  getDutiesForMonth: async (yearMonth: string): Promise<Duty[]> => {
    try {
      const response = await axios.get(`${API_BASE}/duties/month/${yearMonth}`);
      return response.data;
    } catch (error) {
      console.error("獲取月份值班記錄失敗:", error);
      throw error;
    }
  },

  // 獲取指定人員的值班記錄
  getDutiesForPerson: async (person: string): Promise<Duty[]> => {
    const response = await axios.get(`${API_BASE}/duties/person/${person}`);
    return response.data;
  },
  
  // 新增加班記錄
  addDuty: async (dutyData: DutyCreate): Promise<Duty> => {
    const response = await axios.post(`${API_BASE}/duties`, dutyData);
    return response.data;
  },
  
  // 刪除加班記錄
  removeDuty: async (id: string): Promise<void> => {
    const response = await axios.delete(`${API_BASE}/duties/${id}`);
    return response.data;
  },
  
  // 產生報表
  generateReport: async (yearMonth: string): Promise<ReportGenerationResponse> => {
    try {
      const response = await axios.post(`${API_BASE}/generate_report/${yearMonth}`, null, {
        responseType: 'blob'  // 確保響應作為二進制數據處理
      });
      
      // 檢查回應是否為blob
      if (!(response.data instanceof Blob)) {
        throw new Error('回應不是二進制數據');
      }
      
      // 產生下載文件名
      const filename = `overtime_report_${yearMonth}.zip`;
      
      // 使用Blob創建URL供下載
      const blob = new Blob([response.data], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);
      
      // 創建下載連結並觸發
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      
      // 清理
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      return {
        message: '報表產生成功，正在下載...',
        download_url: url,
        generated_files: []
      };
    } catch (error) {
      console.error('產生報表失敗:', error);
      
      // 友好的用戶錯誤訊息
      const errorMessage = error instanceof Error ? error.message : '未知錯誤';
      
      return {
        message: `報表產生失敗: ${errorMessage}`,
        download_url: '',
        generated_files: []
      };
    }
  }
};

// 報表相關API
export const reportApi = {
  // 觸發報表生成
  generateReport: async (yearMonth: string, memberId?: string): Promise<ReportGenerationResponse> => {
    try {
      let url = `${API_BASE}/generate_report/${yearMonth}`;
      let params = {};
      
      if (memberId) {
        params = { member_id: memberId };
      }

      const response = await axios.post(url, null, {
        params: params,
        responseType: 'json' // API返回的是包含路徑的JSON
      });
      
      console.log("Report generation response:", response.data);
      return response.data;
    } catch (error) {
      console.error("報表生成失敗:", error);
      throw error;
    }
  },
  
  // 下載報表文件
  downloadReport: async (filename: string): Promise<Blob> => {
    try {
      const response = await axios.get(`${API_BASE}/download/${filename}`, {
        responseType: 'blob' // 確保響應作為二進制數據處理
      });
      return response.data;
    } catch (error) {
      console.error("下載報表失敗:", error);
      throw error;
    }
  }
}; 