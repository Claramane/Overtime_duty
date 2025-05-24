import React, { useState, useEffect } from 'react';
import { 
  Box, Paper, Typography, Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, TablePagination, TextField, InputAdornment,
  Select, MenuItem, FormControl, InputLabel, Chip, Alert, Snackbar
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import SearchIcon from '@mui/icons-material/Search';
import dayjs, { Dayjs } from 'dayjs';
import { Duty } from '../types';
import { dutyApi } from '../services/api';

// 假資料 - 在 API 完成前使用
const mockDuties: Duty[] = [
  {
    id: '1',
    dateTime: '202410080730',
    hours: 0.5,
    person: '游雅盛',
    reason: '2'
  },
  {
    id: '2',
    dateTime: '202410080730',
    hours: 0.5,
    person: '史若蘭',
    reason: '2'
  },
  {
    id: '3',
    dateTime: '202410080730',
    hours: 0.5,
    person: '吳佩諭',
    reason: '2'
  },
  // 更多假資料...
];

const DutyList: React.FC = () => {
  const [date, setDate] = useState<Dayjs>(dayjs());
  const [duties, setDuties] = useState<Duty[]>([]);
  const [filteredDuties, setFilteredDuties] = useState<Duty[]>([]);
  const [selectedPerson, setSelectedPerson] = useState<string>('all');
  const [searchText, setSearchText] = useState<string>('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [notification, setNotification] = useState<{show: boolean, message: string, type: 'success' | 'error'}>({
    show: false,
    message: '',
    type: 'success'
  });

  // 記錄唯一的人員列表
  const [personList, setPersonList] = useState<string[]>([]);

  // 載入選定月份的值班記錄
  useEffect(() => {
    const yearMonth = date.format('YYYYMM');
    fetchDuties(yearMonth);
  }, [date]);

  // 篩選值班記錄
  useEffect(() => {
    filterDuties();
  }, [duties, selectedPerson, searchText]);

  const fetchDuties = async (yearMonth: string) => {
    try {
      // 實際專案中應使用 API 呼叫
      // const data = await dutyApi.getDutiesForMonth(yearMonth);
      // 暫時使用模擬資料
      const data = mockDuties.filter(d => d.dateTime.startsWith(yearMonth));
      setDuties(data);
      
      // 建立唯一人員列表
      const persons = Array.from(new Set(data.map(duty => duty.person)));
      setPersonList(persons);
    } catch (error) {
      console.error('Failed to fetch duties:', error);
      showNotification('載入值班記錄失敗', 'error');
    }
  };

  const filterDuties = () => {
    let filtered = [...duties];
    
    // 依人員篩選
    if (selectedPerson !== 'all') {
      filtered = filtered.filter(duty => duty.person === selectedPerson);
    }
    
    // 依搜尋文字篩選
    if (searchText.trim() !== '') {
      const searchLower = searchText.toLowerCase();
      filtered = filtered.filter(duty => 
        duty.person.toLowerCase().includes(searchLower) ||
        duty.reason.toLowerCase().includes(searchLower) ||
        duty.dateTime.includes(searchLower)
      );
    }
    
    setFilteredDuties(filtered);
    // 重置分頁到第一頁
    setPage(0);
  };

  const handleDateChange = (newDate: Dayjs | null) => {
    if (newDate) {
      setDate(newDate);
    }
  };

  const handlePersonChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setSelectedPerson(event.target.value as string);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchText(event.target.value);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
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

  // 格式化日期時間
  const formatDateTime = (dateTime: string) => {
    if (dateTime.length < 12) return dateTime;
    const year = dateTime.substring(0, 4);
    const month = dateTime.substring(4, 6);
    const day = dateTime.substring(6, 8);
    const hour = dateTime.substring(8, 10);
    const minute = dateTime.substring(10, 12);
    return `${year}/${month}/${day} ${hour}:${minute}`;
  };

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <DatePicker
            views={['year', 'month']}
            openTo="month"
            value={date}
            onChange={handleDateChange}
            slotProps={{
              textField: {
                size: 'small',
                sx: { minWidth: 150 }
              }
            }}
          />
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>人員</InputLabel>
            <Select
              value={selectedPerson}
              label="人員"
              onChange={(e) => setSelectedPerson(e.target.value as string)}
            >
              <MenuItem value="all">全部</MenuItem>
              {personList.map(person => (
                <MenuItem key={person} value={person}>{person}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
        
        <TextField
          placeholder="搜尋..."
          size="small"
          value={searchText}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ minWidth: 200 }}
        />
      </Box>
      
      <Typography variant="h6" gutterBottom>
        {date.format('YYYY 年 MM 月')}值班記錄
        {selectedPerson !== 'all' && ` - ${selectedPerson}`}
      </Typography>
      
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>日期時間</TableCell>
              <TableCell>人員</TableCell>
              <TableCell>時數</TableCell>
              <TableCell>原因</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredDuties
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((duty) => (
                <TableRow key={duty.id} hover>
                  <TableCell>{duty.id}</TableCell>
                  <TableCell>{formatDateTime(duty.dateTime)}</TableCell>
                  <TableCell>
                    <Chip 
                      label={duty.person} 
                      size="small" 
                      color="primary" 
                      variant="outlined" 
                    />
                  </TableCell>
                  <TableCell>{duty.hours}</TableCell>
                  <TableCell>{duty.reason}</TableCell>
                </TableRow>
              ))}
            {filteredDuties.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  無符合條件的記錄
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      <TablePagination
        rowsPerPageOptions={[5, 10, 25]}
        component="div"
        count={filteredDuties.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        labelRowsPerPage="每頁行數:"
        labelDisplayedRows={({ from, to, count }) => `${from}-${to} / ${count}`}
      />
      
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

export default DutyList; 