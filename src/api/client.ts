import axios from 'axios';

// Ensure baseURL always uses same-origin relative path '/api/v1' in the web app
// and discards any stale localhost:8000 or 127.0.0.1:8000 from the container environment
const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (!envUrl || envUrl.includes('localhost:8000') || envUrl.includes('127.0.0.1:8000')) {
    return '/api/v1';
  }
  return envUrl;
};

// The centralized axios instance
export const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

// We can add interceptors here in the future for Auth tokens
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle global errors here
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);
