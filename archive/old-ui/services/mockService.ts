import axios from 'axios';

// This mock service intercepts axios requests and returns mock data
const setupMockService = () => {
  // Check if we should use mock data (dev environment or specified in query params)
  const useMockData = process.env.NODE_ENV === 'development' || 
                    window.location.search.includes('mock=true');
  
  if (useMockData) {
    // Setup axios interceptor for GET requests
    axios.interceptors.request.use(async (config) => {
      if (config.method?.toLowerCase() === 'get') {
        const mockEndpoint = `/mock-api${config.url}.json`;
        try {
          console.log(`Using mock data from: ${mockEndpoint}`);
          config.url = mockEndpoint;
        } catch (error) {
          console.warn(`No mock data found for: ${config.url}`);
        }
      }
      return config;
    });

    // Setup axios interceptor for POST requests (just return success with mock ID)
    axios.interceptors.response.use(
      response => response,
      async (error) => {
        // Only handle errors from POST requests in mock mode
        if (error.config.method?.toLowerCase() === 'post') {
          console.log(`Mock POST response for: ${error.config.url}`);
          return {
            data: { 
              id: `mock-${Date.now()}`,
              success: true
            }
          };
        }
        return Promise.reject(error);
      }
    );
  }
};

export default setupMockService; 