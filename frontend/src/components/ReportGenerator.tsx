import React, { useState, useEffect } from 'react';
import { 
  Box, Paper, Typography, Button, Grid, Select, MenuItem, 
  FormControl, InputLabel, CircularProgress, Chip, Alert, 
  Snackbar, List, ListItem, ListItemIcon, ListItemText, Link,
  IconButton
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import DescriptionIcon from '@mui/icons-material/Description';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import dayjs, { Dayjs } from 'dayjs';
import { reportApi } from '../services/api';

interface Member {
  id: string;
  name: string;
}

// 假資料 - 在 API 完成前使用
const mockMembers: Member[] = [
  { id: 'A', name: '林怡芸' },
  { id: 'B', name: '游雅盛' },
  { id: 'C', name: '陳燁晨' },
  { id: 'D', name: '顏任軒' },
  { id: 'E', name: '吳佩諭' },
  { id: 'F', name: '史若蘭' },
  { id: 'G', name: '陳品臣' },
  { id: 'H', name: '陳柏羽' }
];

const ReportGenerator: React.FC = () => {
  const [date, setDate] = useState<Dayjs>(dayjs());
  const [selectedMemberId, setSelectedMemberId] = useState<string>('');
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [generatedFiles, setGeneratedFiles] = useState<{ path: string; url: string }[]>([]);
  const [responseMessage, setResponseMessage] = useState<string>('');
  const [notification, setNotification] = useState<{show: boolean, message: string, type: 'success' | 'error'}>({
    show: false,
    message: '',
    type: 'success'
  });

  useEffect(() => {
    // 實際專案中應從 API 獲取成員列表
    setMembers(mockMembers);
  }, []);

  const handleDateChange = (newDate: Dayjs | null) => {
    if (newDate) {
      setDate(newDate);
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

  const handleMemberChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setSelectedMemberId(event.target.value as string);
  };

  const handleGenerateReport = async () => {
    const yearMonth = date.format('YYYYMM');
    
    setLoading(true);
    setGeneratedFiles([]);
    setResponseMessage('');
    
    try {
      // 使用API呼叫
      const response = await reportApi.generateReport(yearMonth, selectedMemberId || undefined);
      setResponseMessage(response.message);
      
      // 添加空值檢查，確保generated_files存在
      if (response.generated_files && response.generated_files.length > 0) {
        setGeneratedFiles(response.generated_files);
        
        showNotification(
          `成功產生 ${response.generated_files.length} 個報表`,
          'success'
        );
      } else if (response.message.includes('失敗')) {
        setGeneratedFiles([]);
        showNotification(response.message, 'error');
      } else {
        // 報表可能已通過API內部邏輯自動下載
        setGeneratedFiles([]);
        showNotification('已開始下載報表', 'success');
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : '未知錯誤';
      console.error('報表產生失敗:', error);
      setResponseMessage(`報表產生失敗: ${errorMsg}`);
      showNotification(`報表產生失敗，請稍後再試: ${errorMsg}`, 'error');
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

  return (
    <Box>
      <Paper 
        elevation={3} 
        sx={{ 
          p: 3, 
          mb: 3, 
          borderRadius: 2,
          borderTop: '4px solid',
          borderColor: 'primary.main' 
        }}
      >
        <Typography variant="h5" component="h2" gutterBottom>
          產生加班時數報表
        </Typography>
        
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={4}>
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
              <IconButton onClick={handlePrevMonth} size="small">
                <ArrowBackIcon />
              </IconButton>
              
              <DatePicker
                views={['month', 'year']}
                openTo="month"
                label="選擇年月"
                value={date}
                onChange={handleDateChange}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    margin: 'normal',
                    size: 'small'
                  }
                }}
              />
              
              <IconButton onClick={handleNextMonth} size="small">
                <ArrowForwardIcon />
              </IconButton>
            </Box>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <FormControl fullWidth margin="normal">
              <InputLabel>選擇成員</InputLabel>
              <Select
                value={selectedMemberId}
                label="選擇成員"
                onChange={(e) => setSelectedMemberId(e.target.value as string)}
              >
                <MenuItem value="">所有成員</MenuItem>
                {members.map(member => (
                  <MenuItem key={member.id} value={member.id}>
                    {member.name} ({member.id})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Box sx={{ mt: 2 }}>
              <Button
                variant="contained"
                color="primary"
                fullWidth
                size="large"
                onClick={handleGenerateReport}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : null}
              >
                {loading ? '產生中...' : '產生報表'}
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>
      
      {responseMessage && (
        <Alert 
          severity={generatedFiles.length > 0 ? 'success' : 'warning'} 
          sx={{ mb: 3 }}
        >
          {responseMessage}
        </Alert>
      )}
      
      {generatedFiles.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            已產生的報表檔案:
          </Typography>
          <List>
            {generatedFiles.map((file, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <DescriptionIcon color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary={file.path.split('/').pop()} 
                  secondary={
                    <Link href={file.url} target="_blank" rel="noopener">
                      下載連結
                    </Link>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
      
      <Box sx={{ mt: 4 }}>
        <Typography variant="subtitle2" color="text.secondary">
          💡 提示
        </Typography>
        <Typography variant="body2" color="text.secondary">
          • 報表產生需要獲取 Google Calendar 事件和手動值班資料。<br />
          • 產生的 Excel 檔案將包含選定月份的所有值班記錄和計算好的工時。<br />
          • 可以選擇產生單一成員或所有成員的報表。<br />
          • 建議使用時確保網路連線穩定以防 API 呼叫中斷。
        </Typography>
      </Box>
      
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

export default ReportGenerator; 