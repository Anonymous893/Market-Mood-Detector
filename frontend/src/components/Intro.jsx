import { Typography, Box } from '@mui/material';

export default function Intro({ 
  title = "Market Mood Detector",
  subtitle = "Track and analyse the performance of the top tech giants."
}) {
  return (
    <Box textAlign="center" mb={6}>
      <Typography variant="h3" fontWeight={600} gutterBottom>
        {title}
      </Typography>
      <Typography variant="subtitle1" color="text.secondary">
        {subtitle}
      </Typography>
    </Box>
  );
}