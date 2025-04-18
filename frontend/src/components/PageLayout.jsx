import { Box } from '@mui/material';

export default function PageLayout({ children }) {
  return (
    <Box sx={{ 
      minHeight: '100vh',
      background: 'linear-gradient(to bottom, #f8faff 0%, #ffffff 100%)',
    }}>
      {children}
    </Box>
  );
}