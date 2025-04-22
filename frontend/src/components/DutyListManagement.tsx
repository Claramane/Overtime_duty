import React, { useState, useEffect, useMemo } from 'react';
import { 
  Box, Paper, Typography, Button, Grid, Checkbox, 
  FormControl, InputLabel, Select, MenuItem, TextField, 
  FormGroup, FormControlLabel, Table, TableBody, TableCell, 
  TableContainer, TableHead, TableRow, IconButton, Alert,
  CircularProgress, Snackbar, Tab, Tabs
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import DeleteIcon from '@mui/icons-material/Delete';
import dayjs, { Dayjs } from 'dayjs';
import { dutyApi } from '../services/api';
import HolidayCalendar from './HolidayCalendar';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';

interface Duty {
  id: string;
  dateTime: string;
  hours: number;
  person: string;
  reason: string;
}

interface DutyPerson {
  value: string;
  label: string;
}

const dutyPersons: DutyPerson[] = [
  { value: "游雅盛", label: "01221 游雅盛" },
  { value: "史若蘭", label: "00013 史若蘭" },
  { value: "吳佩諭", label: "01161 吳佩諭" },
  { value: "林怡芸", label: "01757 林怡芸" },
  { value: "顏任軒", label: "02002 顏任軒" },
  { value: "陳燁晨", label: "02003 陳燁晨" },
  { value: "陳品臣", label: "02106 陳品臣" },
  { value: "陳柏羽", label: "02109 陳柏羽" }
];

const reasonOptions = [
  { value: "1", label: "1. 查巡病房" },
  { value: "2", label: "2. 醫療會議" },
  { value: "3", label: "3. 夜間門診" },
  { value: "4", label: "4. 緊急開刀" },
  { value: "5", label: "5. 受院緊急召回" },
  { value: "6", label: "6. 當班執行醫療業務超時" },
  { value: "7", label: "7. 病房值班" },
  { value: "8", label: "8. ICU值班" },
  { value: "9", label: "9. 急診值班" },
  { value: "10", label: "10. 其他(請敘明原因)" }
];

const DutyListManagement: React.FC = () => {
  // 值班列表相關狀態
  const [duties, setDuties] = useState<Duty[]>([]);
  const [filteredDuties, setFilteredDuties] = useState<Duty[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [currentMonth, setCurrentMonth] = useState<Dayjs | null>(dayjs());

  // 新增加班記錄相關狀態
  const [dutyDate, setDutyDate] = useState<Dayjs | null>(null);
  const [dutyTime, setDutyTime] = useState<string>("00:00");
  const [dutyHours, setDutyHours] = useState<number>(0.5);
  const [selectedPersons, setSelectedPersons] = useState<string[]>([]);
  const [dutyReason, setDutyReason] = useState<string>("");
  const [additionalReason, setAdditionalReason] = useState<string>("");

  // 報表產生相關狀態
  const [reportYearMonth, setReportYearMonth] = useState<Dayjs | null>(dayjs());
  const [reportLoading, setReportLoading] = useState<boolean>(false);
  const [reportMessage, setReportMessage] = useState<string>("");

  // 通知相關狀態
  const [notification, setNotification] = useState<{
    show: boolean;
    message: string;
    type: 'success' | 'error';
  }>({
    show: false,
    message: '',
    type: 'success'
  });

  // 生成可用時間選項
  const availableTimes = useMemo(() => {
    const times = [];
    for (let hour = 0; hour < 24; hour++) {
      for (let minute = 0; minute < 60; minute += 30) {
        times.push(`${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`);
      }
    }
    return times;
  }, []);

  // 計算是否可以新增加班記錄
  const canAddDuty = useMemo(() => {
    return dutyDate && dutyTime && selectedPersons.length > 0 && dutyReason &&
      (dutyReason !== '10' || additionalReason);
  }, [dutyDate, dutyTime, selectedPersons, dutyReason, additionalReason]);

  // 頁面加載時獲取值班記錄
  useEffect(() => {
    fetchDuties(dayjs().format('YYYYMM'));
  }, []);

  // 當月份變更時重新請求數據
  useEffect(() => {
    if (currentMonth) {
      const yearMonth = currentMonth.format('YYYYMM');
      fetchDuties(yearMonth);
    }
  }, [currentMonth]);

  // 獲取值班記錄，根據提供的年月過濾
  const fetchDuties = async (yearMonth: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await dutyApi.getDutiesForMonth(yearMonth);
      setDuties(response);
      setFilteredDuties(response);
    } catch (err) {
      console.error('獲取值班記錄失敗', err);
      setError('獲取值班記錄失敗，請稍後再試');
      showNotification('獲取值班記錄失敗，請稍後再試', 'error');
    } finally {
      setLoading(false);
    }
  };

  // 新增加班記錄
  const addDuty = async () => {
    if (!canAddDuty) return;

    const formattedDate = dutyDate?.format('YYYYMMDD') || '';
    const dutyDateTime = `${formattedDate}${dutyTime.replace(':', '')}`;
    const reasonText = getReasonText(dutyReason);
    
    const dutyRequests = selectedPersons.map(person => ({
      dateTime: dutyDateTime,
      hours: dutyHours,
      person: person,
      reason: additionalReason ? `${reasonText} - ${additionalReason}` : reasonText
    }));

    setLoading(true);
    try {
      for (const request of dutyRequests) {
        await dutyApi.addDuty(request);
      }
      await fetchDuties(dayjs().format('YYYYMM'));
      resetForm();
      showNotification('成功新增加班記錄', 'success');
    } catch (err) {
      console.error('新增加班記錄失敗', err);
      showNotification('新增加班記錄失敗，請稍後再試', 'error');
    } finally {
      setLoading(false);
    }
  };

  // 刪除加班記錄
  const removeDuty = async (id: string) => {
    setLoading(true);
    try {
      await dutyApi.removeDuty(id);
      await fetchDuties(dayjs().format('YYYYMM'));
      showNotification('成功刪除加班記錄', 'success');
    } catch (err) {
      console.error('刪除加班記錄失敗', err);
      showNotification('刪除加班記錄失敗，請稍後再試', 'error');
    } finally {
      setLoading(false);
    }
  };

  // 產生報表
  const generateReport = async () => {
    if (!reportYearMonth) return;
    
    const yearMonth = reportYearMonth.format('YYYYMM');
    setReportLoading(true);
    setReportMessage('');
    
    try {
      const response = await dutyApi.generateReport(yearMonth);
      setReportMessage(response.message || '報表產生完成，準備下載');
      
      // 檢查下載URL是否存在且有效
      if (response.download_url) {
        // 自動下載已經在API內部處理
        showNotification('已開始下載報表', 'success');
      } else if (response.message.includes('失敗')) {
        // 處理錯誤情況
        showNotification(response.message, 'error');
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '未知錯誤';
      console.error('產生報表失敗', err);
      setReportMessage(`產生報表失敗: ${errorMsg}`);
      showNotification(`產生報表失敗: ${errorMsg}`, 'error');
    } finally {
      setReportLoading(false);
    }
  };

  // 重置表單
  const resetForm = () => {
    setDutyDate(null);
    setDutyTime('00:00');
    setDutyHours(0.5);
    setSelectedPersons([]);
    setDutyReason('');
    setAdditionalReason('');
  };

  // 顯示通知
  const showNotification = (message: string, type: 'success' | 'error') => {
    setNotification({
      show: true,
      message,
      type
    });
  };

  // 關閉通知
  const handleCloseNotification = () => {
    setNotification({ ...notification, show: false });
  };

  // 處理人員選擇
  const handlePersonChange = (person: string) => {
    setSelectedPersons(prev => 
      prev.includes(person) 
        ? prev.filter(p => p !== person) 
        : [...prev, person]
    );
  };

  // 格式化日期時間
  const formatDateTime = (dateTimeString: string) => {
    if (!dateTimeString) return '';
    const year = dateTimeString.substring(0, 4);
    const month = dateTimeString.substring(4, 6);
    const day = dateTimeString.substring(6, 8);
    const hour = dateTimeString.substring(8, 10);
    const minute = dateTimeString.substring(10, 12);
    return `${year}-${month}-${day} ${hour}:${minute}`;
  };

  // 獲取原因文字
  const getReasonText = (value: string) => {
    const reason = reasonOptions.find(option => option.value === value);
    return reason ? reason.label : value;
  };

  // 處理標籤頁變更
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // 處理月份變更
  const handleMonthChange = (newMonth: Dayjs | null) => {
    setCurrentMonth(newMonth);
  };

  // 月份前進一個月
  const handleNextMonth = () => {
    if (currentMonth) {
      setCurrentMonth(currentMonth.add(1, 'month'));
    }
  };

  // 月份後退一個月
  const handlePrevMonth = () => {
    if (currentMonth) {
      setCurrentMonth(currentMonth.subtract(1, 'month'));
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="duty management tabs">
          <Tab label="值班列表" />
          <Tab label="下載加班表" />
          <Tab label="假日日曆" />
        </Tabs>
      </Box>

      {/* 值班列表頁面 */}
      <TabPanel value={tabValue} index={0}>
        <Paper elevation={3} sx={{ p: 3, mb: 3, borderRadius: 2 }}>
          <Typography variant="h5" component="h2" gutterBottom>
            新增加班記錄
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <DatePicker
                label="選擇日期"
                views={['month', 'year', 'day']}
                openTo="day"
                value={dutyDate}
                onChange={setDutyDate}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    margin: 'normal'
                  }
                }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel>選擇時間</InputLabel>
                <Select
                  value={dutyTime}
                  label="選擇時間"
                  onChange={(e) => setDutyTime(e.target.value as string)}
                >
                  {availableTimes.map((time) => (
                    <MenuItem key={time} value={time}>
                      {time}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel>時數</InputLabel>
                <Select
                  value={dutyHours}
                  label="時數"
                  onChange={(e) => setDutyHours(Number(e.target.value))}
                >
                  {Array.from({ length: 32 }, (_, i) => i * 0.5 + 0.5).map((hours) => (
                    <MenuItem key={hours} value={hours}>
                      {hours} 小時
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel>加班原因</InputLabel>
                <Select
                  value={dutyReason}
                  label="加班原因"
                  onChange={(e) => setDutyReason(e.target.value as string)}
                >
                  {reasonOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <TextField
                fullWidth
                margin="normal"
                label="加班原因（選填）"
                value={additionalReason}
                onChange={(e) => setAdditionalReason(e.target.value)}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                選擇人員：
              </Typography>
              <FormGroup row>
                {dutyPersons.map((person) => (
                  <FormControlLabel
                    key={person.value}
                    control={
                      <Checkbox
                        checked={selectedPersons.includes(person.value)}
                        onChange={() => handlePersonChange(person.value)}
                      />
                    }
                    label={person.label}
                  />
                ))}
              </FormGroup>
            </Grid>
            
            <Grid item xs={12}>
              <Button
                variant="contained"
                color="primary"
                onClick={addDuty}
                disabled={!canAddDuty || loading}
                sx={{ mt: 2 }}
              >
                {loading ? <CircularProgress size={24} /> : '新增加班記錄'}
              </Button>
            </Grid>
          </Grid>
        </Paper>
        
        <Paper elevation={3} sx={{ p: 3, borderRadius: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h5" component="h2">
              加班記錄列表
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <IconButton onClick={handlePrevMonth} size="small">
                <ArrowBackIcon />
              </IconButton>
              
              <DatePicker
                views={['month', 'year']}
                openTo="month"
                value={currentMonth}
                onChange={handleMonthChange}
                slotProps={{
                  textField: {
                    size: 'small',
                    sx: { mx: 1, width: 150 }
                  }
                }}
              />
              
              <IconButton onClick={handleNextMonth} size="small">
                <ArrowForwardIcon />
              </IconButton>
            </Box>
          </Box>
          
          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
              <CircularProgress />
            </Box>
          )}
          
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          
          {!loading && !error && filteredDuties.length === 0 && (
            <Typography>
              {currentMonth ? `${currentMonth.format('YYYY年MM月')}沒有加班記錄` : '目前沒有加班記錄'}
            </Typography>
          )}
          
          {!loading && !error && filteredDuties.length > 0 && (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>日期時間</TableCell>
                    <TableCell>時數</TableCell>
                    <TableCell>人員</TableCell>
                    <TableCell>原因</TableCell>
                    <TableCell>操作</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredDuties.map((duty) => (
                    <TableRow key={duty.id}>
                      <TableCell>{formatDateTime(duty.dateTime)}</TableCell>
                      <TableCell>{duty.hours}</TableCell>
                      <TableCell>{duty.person}</TableCell>
                      <TableCell>{duty.reason}</TableCell>
                      <TableCell>
                        <IconButton
                          color="error"
                          onClick={() => removeDuty(duty.id)}
                          disabled={loading}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      </TabPanel>

      {/* 報表產生頁面 */}
      <TabPanel value={tabValue} index={1}>
        <Paper elevation={3} sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h5" component="h2" gutterBottom>
            下載加班表
          </Typography>
          
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={6}>
              <DatePicker
                views={['month', 'year']}
                openTo="month"
                label="選擇年月"
                value={reportYearMonth}
                onChange={setReportYearMonth}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    margin: "normal"
                  }
                }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Button
                variant="contained"
                color="primary"
                onClick={generateReport}
                disabled={!reportYearMonth || reportLoading}
                fullWidth
                sx={{ mt: 3, color: 'white' }}
              >
                {reportLoading ? <CircularProgress size={24} /> : '下載加班表'}
              </Button>
            </Grid>
          </Grid>
          
          {reportMessage && (
            <Alert severity="info" sx={{ mt: 3 }}>
              {reportMessage}
            </Alert>
          )}
        </Paper>
      </TabPanel>

      {/* 假日日曆頁面 */}
      <TabPanel value={tabValue} index={2}>
        <HolidayCalendar />
      </TabPanel>

      <Snackbar
        open={notification.show}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseNotification} severity={notification.type} sx={{ width: '100%' }}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

// TabPanel 組件
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`duty-tabpanel-${index}`}
      aria-labelledby={`duty-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

export default DutyListManagement; 