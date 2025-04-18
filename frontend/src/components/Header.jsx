import { IconButton, Typography, Box } from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

export default function Header({ title, onBack }) {
  const navigate = useNavigate();
  
  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      navigate(-1);
    }
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: '16px', mb: 3 }}>
      <IconButton onClick={handleBack} sx={{ p: 0 }}>
        <ArrowBack fontSize="medium" />
      </IconButton>
      <Typography variant="h4"
        sx={{ 
        color: '#3e3b79',
        fontWeight: 600,
        letterSpacing: '-0.5px'
      }}>
        {title}
      </Typography>
    </Box>
  );
}