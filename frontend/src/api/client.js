import axios from 'axios'

// Базовый URL для API Gateway
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Создаем экземпляр axios с базовыми настройками
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Интерцептор для добавления API ключа в заголовки
apiClient.interceptors.request.use(
  (config) => {
    // Если API ключ передан в config.headers, используем его
    if (config.apiKey) {
      config.headers['X-API-Key'] = config.apiKey
      delete config.apiKey
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

export default apiClient
