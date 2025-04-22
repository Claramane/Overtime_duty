// 假日數據結構
export interface Holiday {
  西元日期: string;
  星期: string;
  是否放假: string;
  備註: string;
}

// 加班記錄新增請求結構
export interface DutyCreate {
  dateTime: string;
  hours: number;
  person: string;
  reason: string;
}

// 加班記錄數據結構
export interface Duty {
  id: string;
  dateTime: string;
  hours: number;
  person: string;
  reason: string;
}

// 報表產生響應數據結構
export interface ReportGenerationResponse {
  message: string;
  download_url?: string;
  generated_files?: Array<{
    path: string;
    url: string;
  }>;
} 