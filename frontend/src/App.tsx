import React from 'react';
import { Container, CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import DutyListManagement from './components/DutyListManagement';

// 創建主題
const theme = createTheme({
  palette: {
    primary: {
      main: '#4CAF50',
    },
    secondary: {
      main: '#FFC107',
    },
  },
  typography: {
    fontFamily: [
      '"Microsoft JhengHei"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <LocalizationProvider dateAdapter={AdapterDayjs}>
        <CssBaseline />
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
          <DutyListManagement />
        </Container>
      </LocalizationProvider>
    </ThemeProvider>
  );
}

export default App;
