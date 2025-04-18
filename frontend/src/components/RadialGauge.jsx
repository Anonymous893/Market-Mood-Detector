import { CircularProgress, Box, Typography } from '@mui/material';

const getCategory = (score) => {
  if (score >= 88) return { label: 'Strong Buy', color: '#2e6930' };
  if (score >= 76) return { label: 'Buy', color: '#2d9d92' };
  if (score >= 64) return { label: 'Neutral', color: '#528aae' };
  if (score >= 52) return { label: 'Sell', color: '#b3446c' };
  return { label: 'Strong Sell', color: '#cd1c18' };
};

export default function RadialGauge({ score }) {
  const { label, color } = getCategory(score);

  return (
    <Box sx={{ position: 'relative', display: 'inline-flex', my: 2 }}>
      <CircularProgress
        variant="determinate"
        value={score}
        thickness={6}
        size={100}
        sx={{
          color,
          backgroundColor: '#f5f5f5',
          borderRadius: '50%'
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          bottom: 0,
          right: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column'
        }}
      >
        <Typography variant="subtitle2" component="div" sx={{ fontWeight: 'bold' }}>
          {score.toFixed(1)}
        </Typography>
        <Typography variant="caption" component="div" sx={{ color }}>
          {label}
        </Typography>
      </Box>
    </Box>
  );
}