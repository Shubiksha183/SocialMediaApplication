// services/search.js
import axios from 'axios';
import { getAuthHeaders } from './auth'; // assuming you handle JWT here

export const searchUsers = async (query) => {
  const response = await axios.get(`https://showme-backend-uus3.onrender.com/search/users/?q=${query}`, {
    headers: getAuthHeaders()
  });
  return response.data;
};
