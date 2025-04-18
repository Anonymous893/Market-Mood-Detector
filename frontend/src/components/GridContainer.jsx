import { Box } from '@mui/material';

export default function GridContainer({ children }) {
  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
      {children}
    </Box>
  );
}