import { Box } from '@mui/material';
import StockCard from '../components/StockCard';

export default function StockGrid({ stocks }) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'center',
        gap: 3,
        px: 2,
      }}
    >
      {stocks.map((symbol) => (
        <Box
          key={symbol}
          sx={{
            width: { xs: '100%', sm: '45%', md: '30%', lg: '22%' },
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <StockCard symbol={symbol} />
        </Box>
      ))}
    </Box>
  );
}