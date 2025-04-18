import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Container } from '@mui/material';
import { runAnalysis } from '../services/api';
import PageLayout from '../components/PageLayout';
import Intro from '../components/Intro';
import StockGrid from '../components/StockGrid';
import CTACard from '../components/CTACard';

const MAG7_STOCKS = ['AAPL', 'MSFT', 'NVDA', 'META', 'TSLA', 'AMZN', 'GOOG'];

export default function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = React.useState(false);

  const handleRunAnalysis = async () => {
    setLoading(true);
    try {
      await runAnalysis(MAG7_STOCKS);
      navigate('/analyse');
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageLayout>
      <Container maxWidth="lg" sx={{ 
        py: 6,
        '& .MuiGrid-root': {
          '--grid-spacing': '24px',
          marginTop: 'calc(-1 * var(--grid-spacing))',
          width: 'calc(100% + var(--grid-spacing))'
        }
      }}>
        <Intro />

        <StockGrid stocks={MAG7_STOCKS} />

        <CTACard
          title = "Ready for a deeper dive?"
          subtitle = "Generate a full analysis of all Magnificent 7 stocks with one click."
          buttonText = "Run Full Analysis"
          onButtonClick = { handleRunAnalysis }
          loading = {loading}
        />
      </Container>
    </PageLayout>
  );
}