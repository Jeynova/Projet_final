// client/src/components/TaskList.js
import React, { useState, useEffect } from 'react';

const Client/Src/Components/Tasklist = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/tasks');
      const result = await response.json();
      setData(result.tasks || []);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Handle form submission
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container">
      <h1>Client/Src/Components/Tasklist</h1>
      <form onSubmit={handleSubmit}>
        <input type="text" placeholder="Enter task" />
        <button type="submit">Add Task</button>
      </form>
      <div className="list">
        {data.map((item, index) => (
          <div key={index} className="item">
            {item.title || 'Task'}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Client/Src/Components/Tasklist;
