import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE || 'http://localhost:5000'
});

export const runAnalysis = (stocks) => api.post('/run-analysis', { stocks });
export const fetchCompositeScores = () => api.get('/composite-score');
export const fetchHistoricalData = (stock) => 
  api.get('/historical-scores', { 
    params: { 
      stock: stock
    } 
  });