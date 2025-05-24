import React, { useState, useEffect } from 'react';
import { 
  Box, Paper, Grid, Typography, Button, Dialog, DialogTitle, 
  DialogContent, DialogActions, TextField, FormControl, InputLabel, 
  Select, MenuItem, Alert, Snackbar, IconButton
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import dayjs, { Dayjs } from 'dayjs';
import { Holiday } from '../types';
import { holidayApi } from '../services/api';

// 假日狀態類型
type HolidayStatus = {
  [key: string]: {
    isHoliday: boolean;
    isSpecial: boolean;
    description: string;
  }
};

const HolidayCalendar: React.FC = () => {
  const [date, setDate] = useState<Dayjs>(dayjs());
  const [monthHolidays, setMonthHolidays] = useState<Holiday[]>([]);
  const [holidayStatus, setHolidayStatus] = useState<HolidayStatus>({});
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [currentEditDate, setCurrentEditDate] = useState<string>('');
  const [editStatus, setEditStatus] = useState<string>('0');
  const [editDescription, setEditDescription] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [notification, setNotification] = useState<{show: boolean, message: string, type: 'success' | 'error'}>({
    show: false,
    message: '',
    type: 'success'
  });

  // 載入選定月份的假日
  useEffect(() => {
    const yearMonth = date.format('YYYYMM');
    fetchMonthHolidays(yearMonth);
  }, [date]);

  const fetchMonthHolidays = async (yearMonth: string) => {
    setLoading(true);
    try {
      // 使用API呼叫獲取資料
      const data = await holidayApi.getHolidaysForMonth(yearMonth);
      setMonthHolidays(data);
      
      // 建立假日狀態映射
      const statusMap: HolidayStatus = {};
      data.forEach(holiday => {
        statusMap[holiday.西元日期] = {
          isHoliday: holiday.是否放假 === '2' || holiday.是否放假 === '3',
          isSpecial: holiday.是否放假 === '3',
          description: holiday.備註
        };
      });
      setHolidayStatus(statusMap);
    } catch (error) {
      console.error('載入假日資料失敗:', error);
      showNotification('載入假日資料失敗', 'error');
    } finally {
      setLoading(false);
    }
  };

  // 月份前進一個月
  const handleNextMonth = () => {
    setDate(date.add(1, 'month'));
  };

  // 月份後退一個月
  const handlePrevMonth = () => {
    setDate(date.subtract(1, 'month'));
  };

  const handleMonthChange = (newDate: Dayjs | null) => {
    if (newDate) {
      setDate(newDate);
    }
  };

  const getDaysInMonth = () => {
    const year = date.year();
    const month = date.month();
    const daysInMonth = date.daysInMonth();
    const firstDayOfMonth = dayjs(new Date(year, month, 1));
    const startingDayOfWeek = firstDayOfMonth.day(); // 0 為週日，1 為週一...

    const days = [];
    // 填補月初之前的空格
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }
    // 添加該月的每一天
    for (let i = 1; i <= daysInMonth; i++) {
      const dateStr = date.format('YYYY') + date.format('MM') + String(i).padStart(2, '0');
      days.push({
        date: i,
        dateStr,
        ...holidayStatus[dateStr]
      });
    }
    return days;
  };

  const openEditDialog = (dateStr: string) => {
    setCurrentEditDate(dateStr);
    const status = holidayStatus[dateStr];
    setEditStatus(status?.isHoliday ? (status.isSpecial ? '3' : '2') : '0');
    setEditDescription(status?.description || '');
    setEditDialogOpen(true);
  };

  const handleSaveHolidayStatus = async () => {
    try {
      setLoading(true);
      // 使用API更新假日狀態
      await holidayApi.updateHolidayStatus(currentEditDate, parseInt(editStatus), editDescription);
      
      // 更新本地狀態
      const updatedStatus = {
        ...holidayStatus,
        [currentEditDate]: {
          isHoliday: editStatus === '2' || editStatus === '3',
          isSpecial: editStatus === '3',
          description: editDescription
        }
      };
      setHolidayStatus(updatedStatus);
      setEditDialogOpen(false);
      showNotification('假日狀態更新成功', 'success');
      
      // 重新獲取本月假日資料以確保一致性
      fetchMonthHolidays(date.format('YYYYMM'));
    } catch (error) {
      console.error('更新假日狀態失敗:', error);
      showNotification('更新假日狀態失敗', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showNotification = (message: string, type: 'success' | 'error') => {
    setNotification({
      show: true,
      message,
      type
    });
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, show: false });
  };

  const renderCalendar = () => {
    const days = getDaysInMonth();
    const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
    
    return (
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
          <IconButton onClick={handlePrevMonth} aria-label="上個月">
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h6" sx={{ mx: 2 }} align="center">
            {date.format('YYYY 年 MM 月')}
          </Typography>
          <IconButton onClick={handleNextMonth} aria-label="下個月">
            <ArrowForwardIcon />
          </IconButton>
        </Box>
        <Grid container spacing={0.5}>
          {weekDays.map((day, index) => (
            <Grid item xs={1.7143} key={`header-${index}`}>
              <Box
                sx={{ 
                  p: 1, 
                  textAlign: 'center',
                  bgcolor: 'primary.main',
                  color: 'white',
                  borderRadius: '4px 4px 0 0'
                }}
              >
                {day}
              </Box>
            </Grid>
          ))}
          
          {days.map((day, index) => (
            <Grid item xs={1.7143} key={`day-${index}`}>
              {day ? (
                <Box 
                  sx={{ 
                    p: 1,
                    textAlign: 'center',
                    height: '70px',
                    display: 'flex',
                    flexDirection: 'column',
                    cursor: 'pointer',
                    bgcolor: day.isHoliday ? (day.isSpecial ? '#bbdefb' : '#ffcdd2') : 'white',
                    border: '1px solid',
                    borderColor: day.isHoliday ? (day.isSpecial ? '#64b5f6' : '#ef9a9a') : 'grey.300',
                    borderRadius: '2px',
                    transition: 'all 0.2s',
                    '&:hover': {
                      bgcolor: 'action.hover',
                      borderColor: 'primary.main',
                    }
                  }}
                  onClick={() => openEditDialog(day.dateStr)}
                >
                  <Typography variant="body1" fontWeight="bold">
                    {day.date}
                  </Typography>
                  {day.description && (
                    <Typography variant="caption" noWrap>
                      {day.description}
                    </Typography>
                  )}
                </Box>
              ) : (
                <Box
                  sx={{ 
                    p: 1, 
                    textAlign: 'center',
                    height: '70px',
                    bgcolor: 'grey.50',
                    border: '1px dashed',
                    borderColor: 'grey.200',
                    borderRadius: '2px'
                  }}
                />
              )}
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  };

  return (
    <Box>
      <Box sx={{ p: 3, mb: 3, borderRadius: 2, border: '1px solid', borderColor: 'grey.300' }}>
        <Typography variant="h5" component="h2" gutterBottom>
          假日日曆管理
        </Typography>
        
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
          <DatePicker
            views={['month', 'year']}
            openTo="month"
            value={date}
            onChange={handleMonthChange}
            slotProps={{
              textField: {
                size: 'small',
                fullWidth: true,
                sx: { maxWidth: 200 }
              }
            }}
          />
        </Box>
        
        {renderCalendar()}
      </Box>
      
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)}>
        <DialogTitle>編輯假日狀態</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <Typography variant="body1" gutterBottom>
              日期: {currentEditDate ? `${currentEditDate.substring(0, 4)}/${currentEditDate.substring(4, 6)}/${currentEditDate.substring(6, 8)}` : ''}
            </Typography>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>狀態</InputLabel>
              <Select
                value={editStatus}
                label="狀態"
                onChange={(e) => setEditStatus(e.target.value)}
              >
                <MenuItem value="0">工作日</MenuItem>
                <MenuItem value="2">假日</MenuItem>
                <MenuItem value="3">特殊日 (視為假日)</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              fullWidth
              margin="normal"
              label="備註"
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>取消</Button>
          <Button onClick={handleSaveHolidayStatus} variant="contained" disabled={loading}>
            {loading ? '儲存中...' : '儲存'}
          </Button>
        </DialogActions>
      </Dialog>
      
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

export default HolidayCalendar; 