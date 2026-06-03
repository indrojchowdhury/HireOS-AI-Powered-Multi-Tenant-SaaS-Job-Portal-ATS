import axios from 'axios';

// Set up the base configuration for backend communication
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:9000', // Backend root host for both API and non-API routes
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatically inject JWT token into requests if available
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Allow browser to set the correct multipart boundary when uploading files.
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default apiClient;