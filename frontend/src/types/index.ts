// 假日資料類型
export interface Holiday {
  西元日期: string;  // 格式: YYYYMMDD
  星期: string;      // 一, 二, 三...
  是否放假: string;   // 0: 工作日, 1: 休息日, 2: 假日, 3: 特殊日
  備註: string;
}

// 值班資料類型
export interface Duty {
  id: string;
  dateTime: string;  // 格式: YYYYMMDDHHMM
  hours: number;
  person: string;
  reason: string;
}

// 創建值班資料類型
export interface DutyCreate {
  dateTime: string;  // 格式: YYYYMMDDHHMM
  hours: number;
  person: string;
  reason: string;
}

// 報表生成響應類型
export interface ReportGenerationResponse {
  message: string;
  download_url?: string;
  generated_files: {
    path: string;
    url: string;
  }[];
}

// 月份設定
export interface MonthSettings {
  year: number;
  month: number;
} 