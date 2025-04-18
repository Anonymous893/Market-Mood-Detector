import { Card, Typography, Box, Avatar } from '@mui/material';

export default function StockCard({ symbol }) {
  const logoUrl = `/logos/${symbol.toLowerCase()}.png`;

  return (
    <Card
      sx={{
        p: 2,
        display: 'flex',
        alignItems: 'center',
        gap: 1.5,
        boxShadow: 2,
        width: 200,
        height: 100,
        boxSizing: 'border-box',
        transition: 'transform 0.2s ease-in-out',
        '&:hover': {
          transform: 'scale(1.03)',
        }
      }}
    >
      <Avatar
        src={logoUrl}
        alt={symbol}
        sx={{ 
          width: 48, 
          height: 48,
          flexShrink: 0
        }}
      />
      <Box sx={{ 
        minWidth: 0,
        flexGrow: 1 
      }}>
        <Typography 
          variant="h6" 
          sx={{ 
            fontWeight: 600,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis'
          }}
        >
          {symbol}
        </Typography>
        <Typography 
          variant="body2" 
          color="text.secondary"
          sx={{
            lineHeight: 1.3,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden'
          }}
        >
          {getCompanyName(symbol)}
        </Typography>
      </Box>
    </Card>
  );
}

function getCompanyName(symbol) {
  const names = {
    AAPL: 'Apple Inc.',
    MSFT: 'Microsoft Corp.',
    NVDA: 'NVIDIA Corp.',
    META: 'Meta Platforms',
    TSLA: 'Tesla Inc.',
    AMZN: 'Amazon.com Inc.',
    GOOG: 'Alphabet Inc.',
  };
  return names[symbol] || symbol;
}