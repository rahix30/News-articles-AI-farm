import React, { useState } from 'react';
import {
  Container,
  TextField,
  Button,
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Paper,
  Divider,
  IconButton,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import axios from 'axios';

function App() {
  const [personOfInterest, setPersonOfInterest] = useState('');
  const [query, setQuery] = useState('');
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copySuccess, setCopySuccess] = useState({});
  const [progress, setProgress] = useState(0);
  const [progressText, setProgressText] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setArticles([]);
    setProgress(0);
    setProgressText('Fetching news articles...');
    
    try {
      // Start progress at 10%
      setProgress(10);
      
      const response = await axios.post('http://localhost:8001/api/articles', {
        person_of_interest: personOfInterest,
        query: query,
      });
      
      // Process articles one by one with progress updates
      const receivedArticles = response.data.articles;
      const totalArticles = receivedArticles.length;
      
      // Calculate progress steps
      const progressPerArticle = 80 / totalArticles; // Reserve 10% for start and end
      
      const processedArticles = [];
      for (let i = 0; i < receivedArticles.length; i++) {
        const article = receivedArticles[i];
        processedArticles.push(article);
        
        // Update progress
        const currentProgress = 10 + ((i + 1) * progressPerArticle);
        setProgress(currentProgress);
        setProgressText(`Processing article ${i + 1} of ${totalArticles}...`);
        
        // Add a small delay to show progress (optional)
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Update articles state to show them appearing one by one
        setArticles([...processedArticles]);
      }
      
      // Complete the progress
      setProgress(100);
      setProgressText('All articles processed successfully!');
      
      // Clear progress text after a delay
      setTimeout(() => {
        setProgressText('');
      }, 2000);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred while fetching articles');
      setProgress(0);
      setProgressText('');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (article, index) => {
    try {
      await navigator.clipboard.writeText(article.modified_content);
      setCopySuccess(prev => ({ ...prev, [index]: true }));
      setTimeout(() => {
        setCopySuccess(prev => ({ ...prev, [index]: false }));
      }, 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom align="center">
        News Articles AI Modifier
      </Typography>
      
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Person of Interest"
                value={personOfInterest}
                onChange={(e) => setPersonOfInterest(e.target.value)}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Search Query (Optional)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                fullWidth
                variant="contained"
                type="submit"
                disabled={loading}
                sx={{ py: 1.5 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Generate Modified Articles'}
              </Button>
            </Grid>
          </Grid>
        </form>
      </Paper>

      {/* Progress Section */}
      {(loading || progress > 0) && (
        <Box sx={{ width: '100%', mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              {progressText}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {Math.round(progress)}%
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={progress} 
            sx={{
              height: 8,
              borderRadius: 4,
              '& .MuiLinearProgress-bar': {
                borderRadius: 4,
              },
            }}
          />
        </Box>
      )}

      {error && (
        <Typography color="error" align="center" gutterBottom>
          {error}
        </Typography>
      )}

      <Grid container spacing={3}>
        {articles.map((article, index) => (
          <Grid item xs={12} key={index}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h5">
                    {article.modified_title}
                  </Typography>
                  <Tooltip title={copySuccess[index] ? "Copied!" : "Copy modified content"}>
                    <IconButton 
                      onClick={() => handleCopy(article, index)}
                      color={copySuccess[index] ? "success" : "primary"}
                      size="small"
                    >
                      <ContentCopyIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Source: {article.source} | Published: {new Date(article.published_at).toLocaleDateString()}
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Original Content:
                </Typography>
                <Typography paragraph>
                  {article.original_content}
                </Typography>
                <Typography variant="h6" gutterBottom>
                  Modified Content:
                </Typography>
                <Typography paragraph>
                  {article.modified_content}
                </Typography>
                <Button
                  variant="outlined"
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Read Original Article
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
}

export default App; 