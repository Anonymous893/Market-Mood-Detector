import { Box, CircularProgress } from '@mui/material';

export default function LoadingOverlay({ loading }) {
  if (!loading) return null;

  return (
    <Box sx={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(255, 255, 255, 0.7)',
      zIndex: 999,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <CircularProgress size={60} thickness={4} />
    </Box>
  );
}