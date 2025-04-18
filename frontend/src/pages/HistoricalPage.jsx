import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Typography } from '@mui/material';
import Header from '../components/Header';
import DataCard from '../components/DataCard';
import GridContainer from '../components/GridContainer';
import { fetchHistoricalData } from '../services/api';
import PageLayout from '../components/PageLayout';
import LoadingOverlay from '../components/LoadingOverlay';
import ContentContainer from '../components/ContentContainer';

export default function HistoricalPage() {
  const { stock } = useParams();
  const [historicalData, setHistoricalData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const response = await fetchHistoricalData(stock);
        setHistoricalData(response.data.scores);
      } catch (error) {
        console.error('Failed to load historical data:', error);
      }
      setLoading(false);
    };
    loadData();
  }, [stock]);

  return (
    <PageLayout>
      <LoadingOverlay loading={ loading } />

      <ContentContainer>
        <Header title={`${stock} Historical Data`} />

        {/* <Card sx={{ p: 2, mb: 4, backgroundColor: '#f8faff'}}> */}
        <Typography variant="h6" gutterBottom>Composite Score Trend</Typography>
        <div style={{ height: '300px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="composite_score" stroke="#8884d8" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        {/* </Card> */}

        <GridContainer>
          {historicalData.map((day) => (
            <DataCard
              key={day.date}
              title={new Date(day.date).toLocaleDateString()}
              data={{
                'Score': day.composite_score.toFixed(2),
                'Sentiment': `${(day.sentiment * 100).toFixed(1)}%`,
                'VIX': day.vix.toFixed(1),
              }}
              sx={{ backgroundColor: '#f5f5f5' }}
            />
          ))}
        </GridContainer>
      </ContentContainer>
    </PageLayout>
  );
}