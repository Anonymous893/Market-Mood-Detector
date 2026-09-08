import { useState, useCallback, useRef, useEffect } from 'react';
import { analyzeTicker, getApiErrorMessage } from '../services/api';
import { useRecentSearches } from './useRecentSearches';

const PHASES = [
  'Fetching Yahoo Finance news…',
  'Deduplicating articles…',
  'Running FinBERT sentiment analysis…',
  'Computing market mood & confidence…',
  'Preparing the dashboard…',
];

const PHASE_DELAYS = [0, 2500, 5000, 7500, 10000];

export function useAnalysis() {
  const [ticker, setTicker] = useState('');
  const [loading, setLoading] = useState(false);
  const [phase, setPhase] = useState('');
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const timers = useRef([]);
  const requestId = useRef(0);
  const { recentSearches, addRecent } = useRecentSearches();

  const clearTimers = useCallback(() => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  }, []);

  useEffect(() => () => clearTimers(), [clearTimers]);

  const analyze = useCallback(async (symbol) => {
    const sym = (symbol ?? ticker).trim().toUpperCase();
    if (!sym) {
      setError('Please enter a ticker symbol.');
      return;
    }

    const currentRequest = ++requestId.current;
    clearTimers();
    setLoading(true);
    setError('');
    setData(null);
    setPhase(PHASES[0]);

    PHASE_DELAYS.slice(1).forEach((delay, i) => {
      timers.current.push(setTimeout(() => {
        if (currentRequest === requestId.current) setPhase(PHASES[i + 1]);
      }, delay));
    });

    try {
      const result = await analyzeTicker(sym);
      if (currentRequest !== requestId.current) return;

      clearTimers();
      setPhase(PHASES[4]);
      setData(result);
      addRecent(sym);
    } catch (err) {
      if (currentRequest !== requestId.current) return;

      clearTimers();
      setError(getApiErrorMessage(err));
    } finally {
      if (currentRequest === requestId.current) {
        setLoading(false);
        setPhase('');
      }
    }
  }, [ticker, addRecent, clearTimers]);

  return { ticker, setTicker, loading, phase, data, error, analyze, recentSearches };
}
