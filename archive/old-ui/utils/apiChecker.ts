import { API_BASE_URL } from '../config';

/**
 * Checks if the API is accessible
 * @returns Promise that resolves to true if accessible, false otherwise
 */
export const checkApiConnection = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Timeout after 3 seconds
      signal: AbortSignal.timeout(3000),
    });
    
    return response.ok;
  } catch (error) {
    console.warn('API connection check failed:', error);
    return false;
  }
};

/**
 * Displays a warning banner if the API is not accessible
 */
export const showApiWarningIfNeeded = async () => {
  try {
    const isConnected = await checkApiConnection();
    
    if (!isConnected) {
      const warningDiv = document.createElement('div');
      warningDiv.style.position = 'fixed';
      warningDiv.style.top = '0';
      warningDiv.style.left = '0';
      warningDiv.style.right = '0';
      warningDiv.style.backgroundColor = '#FFA500';
      warningDiv.style.color = '#000';
      warningDiv.style.padding = '10px';
      warningDiv.style.textAlign = 'center';
      warningDiv.style.zIndex = '9999';
      warningDiv.innerHTML = `
        <strong>Warning:</strong> Unable to connect to the backend API at <code>${API_BASE_URL}</code>. 
        The UI will use mock data for demonstration purposes. Some features may not work properly.
      `;
      
      document.body.appendChild(warningDiv);
      
      // Enable mock API data automatically
      window.localStorage.setItem('USE_MOCK_API', 'true');
      (window as any).USE_MOCK_API = true;
    }
  } catch (error) {
    console.error('Error in API warning check:', error);
    // Ensure UI doesn't block even if this check fails
    window.localStorage.setItem('USE_MOCK_API', 'true');
    (window as any).USE_MOCK_API = true;
  }
};

/**
 * Use this function to get either mock data or real data
 * based on API availability
 * @param mockData Mock data to return if API is not available
 * @param apiFn Function to call to get real data
 */
export const getDataWithFallback = async <T>(mockData: T, apiFn: () => Promise<T>): Promise<T> => {
  if ((window as any).USE_MOCK_API || window.localStorage.getItem('USE_MOCK_API') === 'true') {
    return Promise.resolve(mockData);
  }
  
  try {
    return await apiFn();
  } catch (error) {
    console.warn('API call failed, using mock data:', error);
    window.localStorage.setItem('USE_MOCK_API', 'true');
    (window as any).USE_MOCK_API = true;
    return mockData;
  }
}; 