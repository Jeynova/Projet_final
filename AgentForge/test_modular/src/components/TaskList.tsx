// @flow

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useTasksContext } from '../hooks/useTasks';
import TaskListSkeleton from './TaskListSkeleton';

type Task = {
  id: number,
  title: string,
  description: string,
  category_id: number,
  user_id: number,
  created_at: Date
};

const TaskList = () => {
  const { userId } = useParams();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const { getTaskCategory, getUser } = useTasksContext();

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/tasks', {
          params: { user_id: userId },
          headers: {
            'Content-Type': 'application/json'
          }
        });
        setTasks(response.data.tasks);
        setLoading(false);
      } catch (error) {
        toast.error(error.message);
        setLoading(false);
      }
    };
    fetchTasks();
  }, [userId]);

  const handleTaskDelete = async (taskId: number) => {
    try {
      await axios.delete(`/api/tasks/${taskId}`);
      setTasks(tasks.filter((task) => task.id !== taskId));
      toast.success('Task deleted successfully');
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleTaskUpdate = async (taskId: number, title: string, description: string) => {
    try {
      await axios.patch(`/api/tasks/${taskId}`, { title, description });
      setTasks(
        tasks.map((task) =>
          task.id === taskId ? { ...task, title, description } : task
        )
      );
      toast.success('Task updated successfully');
    } catch (error) {
      toast.error(error.message);
    }
  };

  return (
    <div className="container">
      <h2>Task List</h2>
      <button
        type="button"
        className="btn btn-primary mb-3"
        onClick={() => console.log('Add new task button clicked')}
      >
        Add New Task
      </button>

      {loading ? (
        <TaskListSkeleton />
      ) : tasks.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>Category</th>
              <th>Title</th>
              <th>Description</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr key={task.id}>
                <td>{getTaskCategory(task.category_id).name}</td>
                <td>{task.title}</td>
                <td>{task.description}</td>
                <td>
                  <button
                    type="button"
                    className="btn btn-danger"
                    onClick={() => handleTaskDelete(task.id)}
                  >
                    Delete
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary ms-3"
                    onClick={() =>
                      handleTaskUpdate(
                        task.id,
                        'Updated title',
                        'Updated description'
                      )
                    }
                  >
                    Update
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>No tasks available</p>
      )}
    </div>
  );
};

export default TaskList;