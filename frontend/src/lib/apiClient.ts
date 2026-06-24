import axios from 'axios';
import { useAuthStore } from './authStore';

const apiClient = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach Token
apiClient.interceptors.request.use(
  (config) => {
    const { tokens } = useAuthStore.getState();
    if (tokens?.access_token) {
      config.headers['Authorization'] = `Bearer ${tokens.access_token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle 401 & Refresh Token
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Check if the error is 401, not a retry, and not on the login/refresh endpoints themselves
    if (
      error.response?.status === 401 && 
      !originalRequest._retry && 
      !originalRequest.url.includes('/auth/login') &&
      !originalRequest.url.includes('/auth/refresh')
    ) {
      originalRequest._retry = true;
      const { tokens, updateTokens, clearAuth } = useAuthStore.getState();
      
      if (tokens?.refresh_token) {
        try {
          const response = await axios.post('/auth/refresh', {
            refresh_token: tokens.refresh_token
          });
          
          if (response.data?.tokens) {
            updateTokens(response.data.tokens);
            // Retry the original request
            originalRequest.headers['Authorization'] = `Bearer ${response.data.tokens.access_token}`;
            return apiClient(originalRequest);
          }
        } catch (refreshError) {
          // If refresh fails, log the user out
          clearAuth();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        clearAuth();
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
