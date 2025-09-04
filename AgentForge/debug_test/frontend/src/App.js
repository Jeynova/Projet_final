import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPosts();
    checkAuthStatus();
  }, []);

  const fetchPosts = async () => {
    try {
      const response = await axios.get('/api/posts');
      setPosts(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching posts:', error);
      setLoading(false);
    }
  };

  const checkAuthStatus = async () => {
    const token = localStorage.getItem('authToken');
    if (token) {
      try {
        const response = await axios.get('/api/auth/profile', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUser(response.data);
      } catch (error) {
        localStorage.removeItem('authToken');
      }
    }
  };

  const handleLogin = async (credentials) => {
    try {
      const response = await axios.post('/api/auth/login', credentials);
      localStorage.setItem('authToken', response.data.token);
      setUser(response.data.user);
    } catch (error) {
      throw error;
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    setUser(null);
  };

  return (
    <div className="App">
      <Header user={user} onLogin={handleLogin} onLogout={handleLogout} />
      <main>
        {loading ? (
          <div className="loading">Loading...</div>
        ) : (
          <Dashboard posts={posts} user={user} onPostUpdate={fetchPosts} />
        )}
      </main>
    </div>
  );
}

export default App;