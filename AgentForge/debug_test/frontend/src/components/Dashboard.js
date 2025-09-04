import React, { useState } from 'react';
import './Dashboard.css';

function Dashboard({ posts, user, onPostUpdate }) {
  const [selectedPost, setSelectedPost] = useState(null);

  const handlePostClick = (post) => {
    setSelectedPost(post);
  };

  const handleCreatePost = async () => {
    if (!user) return;
    
    const title = prompt('Post title:');
    if (title) {
      try {
        const response = await fetch('/api/posts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          },
          body: JSON.stringify({
            title,
            content: 'New post content...',
            author: user._id
          })
        });
        
        if (response.ok) {
          onPostUpdate();
        }
      } catch (error) {
        console.error('Error creating post:', error);
      }
    }
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Recent Posts</h2>
        {user && (
          <button onClick={handleCreatePost} className="btn btn-primary">
            Create Post
          </button>
        )}
      </div>
      
      <div className="posts-grid">
        {posts.map(post => (
          <div 
            key={post._id} 
            className="post-card"
            onClick={() => handlePostClick(post)}
          >
            <h3>{post.title}</h3>
            <p className="post-excerpt">
              {post.content?.substring(0, 150)}...
            </p>
            <div className="post-meta">
              <span>By {post.author?.name}</span>
              <span>{new Date(post.createdAt).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
      </div>
      
      {posts.length === 0 && (
        <div className="empty-state">
          <p>No posts yet. Create your first post!</p>
        </div>
      )}
    </div>
  );
}

export default Dashboard;