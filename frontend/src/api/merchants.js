import apiClient from './client'

/**
 * Создать новый магазин
 * @param {string|Object} nameOrData - Название магазина (строка) или объект с данными {name, logo_url, ...}
 * @returns {Promise} Ответ от сервера с данными созданного магазина
 */
export const createMerchant = async (nameOrData) => {
  try {
    // Пробуем сначала через gateway, если не работает - через merchant-service напрямую
    const merchantServiceUrl = import.meta.env.VITE_MERCHANT_SERVICE_URL || 'http://localhost:8001'
    
    // Поддерживаем как старый формат (только имя), так и новый (объект)
    const merchantData = typeof nameOrData === 'string' 
      ? { name: nameOrData }
      : nameOrData
    
    const response = await apiClient.post('/api/v1/merchants', merchantData, {
      baseURL: merchantServiceUrl
    })
    return response.data
  } catch (error) {
    // Если запрос через gateway не прошел, пробуем через merchant-service
    if (error.response?.status === 404 || error.code === 'ECONNREFUSED') {
      const merchantServiceUrl = import.meta.env.VITE_MERCHANT_SERVICE_URL || 'http://localhost:8001'
      const merchantData = typeof nameOrData === 'string' 
        ? { name: nameOrData }
        : nameOrData
      const response = await apiClient.post('/api/v1/merchants', merchantData, {
        baseURL: merchantServiceUrl
      })
      return response.data
    }
    throw error
  }
}

/**
 * Получить дашборд мерчанта
 * @param {string} apiKey - API ключ мерчанта
 * @returns {Promise} Ответ от сервера с данными дашборда
 */
export const getDashboard = async (apiKey) => {
  try {
    const merchantServiceUrl = import.meta.env.VITE_MERCHANT_SERVICE_URL || 'http://localhost:8001'
    
    // Получаем HTML дашборда (путь /api/v1/dashboard в merchant-service)
    const dashboardResponse = await apiClient.get('/api/v1/dashboard', {
      apiKey,
      baseURL: merchantServiceUrl
    })
    
    // Также получаем список платежей для отображения в таблице
    // Сначала получаем информацию о мерчанте
    const merchantInfo = await apiClient.get('/api/v1/merchants/me', {
      apiKey,
      baseURL: merchantServiceUrl
    })
    
    const merchantId = merchantInfo.data.id
    
    // Получаем платежи
    const paymentServiceUrl = import.meta.env.VITE_PAYMENT_SERVICE_URL || 'http://localhost:8002'
    const paymentsResponse = await apiClient.get(`/api/v1/payments/by-merchant/${merchantId}`, {
      baseURL: paymentServiceUrl
    })
    
    return {
      merchant: merchantInfo.data,
      payments: paymentsResponse.data,
      dashboardHtml: dashboardResponse.data
    }
  } catch (error) {
    throw error
  }
}

/**
 * Получить все мерчанты
 * @returns {Promise} Список всех мерчантов
 */
export const getAllMerchants = async () => {
  try {
    const merchantServiceUrl = import.meta.env.VITE_MERCHANT_SERVICE_URL || 'http://localhost:8001'
    
    const response = await apiClient.get('/api/v1/merchants/all', {
      baseURL: merchantServiceUrl
    })
    
    return response.data
  } catch (error) {
    throw error
  }
}

/**
 * Обновить информацию о мерчанте
 * @param {string} apiKey - API ключ мерчанта
 * @param {Object} updateData - Данные для обновления (logo_url, primary_color, background_color, etc.)
 * @returns {Promise} Обновленные данные мерчанта
 */
export const updateMerchant = async (apiKey, updateData) => {
  try {
    const merchantServiceUrl = import.meta.env.VITE_MERCHANT_SERVICE_URL || 'http://localhost:8001'
    
    const response = await apiClient.patch('/api/v1/merchants/me', updateData, {
      apiKey,
      baseURL: merchantServiceUrl
    })
    
    return response.data
  } catch (error) {
    throw error
  }
}
