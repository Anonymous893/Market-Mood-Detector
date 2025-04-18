import React, { useEffect, useState } from 'react';
import { fetchCompositeScores } from '../services/api';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import DataCard from '../components/DataCard';
import GridContainer from '../components/GridContainer';
import RadialGauge from '../components/RadialGauge';
import PageLayout from '../components/PageLayout';
import LoadingOverlay from '../components/LoadingOverlay';
import ContentContainer from '../components/ContentContainer';

export default function AnalysisPage() {
  const navigate = useNavigate();
  const [scores, setScores] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const response = await fetchCompositeScores();
        setScores(response.data.scores);
      } catch (error) {
        console.error('Failed to load scores:', error);
      }
      setLoading(false);
    };
    loadData();
  }, []);

  return (
    <PageLayout>
      <LoadingOverlay loading={ loading } />

      <ContentContainer>
        <Header title="Analysis Results" onBack={() => navigate('/')} />

        <GridContainer>
          {scores.map((stock) => {
            const score = stock.composite_score;
            return (
              <DataCard
                key={stock.stock}
                title={stock.stock}
                data={{
                  'Sentiment': `${(stock.sentiment * 100).toFixed(1)}%`,
                  'VIX': stock.vix.toFixed(1)
                }}
                gauge={<RadialGauge score={score} />}
                sx={{ backgroundColor: '#f5f5f5', '&:hover': { transform: 'translateY(-4px)' }, }}
                onClick={() => navigate(`/historical/${stock.stock}`)}
              />
            );
          })}
        </GridContainer>
      </ContentContainer>
    </PageLayout>
  );
}