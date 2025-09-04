import React from 'react';
import './Header.css';

function Header({ user, onLogin, onLogout }) {
  return (
    <header className="header">
      <div className="container">
        <h1 className="logo">BlogPlatform</h1>
        <nav className="nav">
          {user ? (
            <div className="user-menu">
              <span>Welcome, {user.name}</span>
              <button onClick={onLogout} className="btn btn-outline">
                Logout
              </button>
            </div>
          ) : (
            <div className="auth-buttons">
              <button 
                onClick={() => onLogin({ email: 'demo@example.com', password: 'demo' })}
                className="btn btn-primary"
              >
                Login
              </button>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Header;