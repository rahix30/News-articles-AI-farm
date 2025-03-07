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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post('http://localhost:8001/api/articles', {
        person_of_interest: personOfInterest,
        query: query,
      });
      
      setArticles(response.data.articles);
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred while fetching articles');
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