import { Card, Typography } from '@mui/material';

export default function DataCard({ title, data, onClick, gauge, sx }) {
  return (
    <Card 
      onClick={onClick} 
      sx={{ 
        p: 2, 
        cursor: onClick ? 'pointer' : 'default',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        transition: 'transform 0.2s',
        ...sx,
      }}
    >
      <Typography variant="h6" sx={{ mb: 1 }}>{title}</Typography>
      {gauge}
      {Object.entries(data).map(([key, value]) => (
        <Typography key={key} variant="body2" sx={{ textAlign: 'center' }}>
          {`${key}: ${value}`}
        </Typography>
      ))}
    </Card>
  );
}