import { 
    Card, 
    CardContent, 
    Typography, 
    Divider, 
    Button 
  } from '@mui/material';
  
  export default function CTACard({ 
    title, 
    subtitle, 
    buttonText, 
    onButtonClick, 
    loading 
  }) {
    return (
      <Card sx={{ 
        mt: 6,
        px: 4,
        py: 5,
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: 3,
        transition: 'all 0.3s ease',
        background: `linear-gradient(15deg, #f8f9fa 0%, #e9ecef 100%)`,
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: `linear-gradient(120deg, 
            rgba(255,255,255,0.15) 25%,
            rgba(0,0,0,0.03) 100%)`,
          zIndex: -1
        },
      }}>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            {title}
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            {subtitle}
          </Typography>
          <Divider sx={{ my: 2, bgcolor: 'rgba(0, 0, 0, 0.12)' }} />
          <Button
            variant="contained"
            sx={{
              backgroundColor: '#3e3b79',
              '&:hover': {
                backgroundColor: '#001528',
                boxShadow: 2
              },
              color: '#ffffff',
              fontWeight: 600,
              px: 4,
              py: 1.5
            }}
            onClick={onButtonClick}
            disabled={loading}
            size="large"
          >
            {loading ? 'Analysing...' : buttonText}
          </Button>
        </CardContent>
      </Card>
    );
  }