import apiClient from './client'

/**
 * Создать новый платеж
 * @param {string} apiKey - API ключ мерчанта
 * @param {Object} paymentData - Данные платежа
 * @param {string|number} paymentData.amount - Сумма платежа
 * @param {string} paymentData.currency - Валюта (например, 'RUB')
 * @param {string} paymentData.description - Описание платежа
 * @param {string} paymentData.payment_method - Метод оплаты (по умолчанию 'card')
 * @returns {Promise} Ответ от сервера с данными созданного платежа
 */
export const createPayment = async (apiKey, paymentData) => {
  try {
    // Gateway работает на порту 8000, путь /v1/payments
    const gatewayUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    
    // Сначала получаем информацию о мерчанте для получения merchant_id
    const merchantServiceUrl = import.meta.env.VITE_MERCHANT_SERVICE_URL || 'http://localhost:8001'
    const merchantResponse = await apiClient.get('/api/v1/merchants/me', {
      apiKey,
      baseURL: merchantServiceUrl
    })
    
    const merchantId = merchantResponse.data.id
    
    // Создаем платеж через gateway
    const response = await apiClient.post('/v1/payments', {
      merchant_id: merchantId,
      amount: String(paymentData.amount),
      currency: paymentData.currency,
      description: paymentData.description,
      payment_method: paymentData.payment_method || 'card'
    }, {
      apiKey,
      baseURL: gatewayUrl
    })
    
    return response.data
  } catch (error) {
    throw error
  }
}

/**
 * Получить все платежи за период
 * @param {string} dateFrom - Дата начала (YYYY-MM-DD)
 * @param {string} dateTo - Дата окончания (YYYY-MM-DD)
 * @returns {Promise} Список платежей
 */
export const getAllPayments = async (dateFrom, dateTo) => {
  try {
    const paymentServiceUrl = import.meta.env.VITE_PAYMENT_SERVICE_URL || 'http://localhost:8002'
    
    const response = await apiClient.get('/api/v1/payments/all', {
      baseURL: paymentServiceUrl,
      params: {
        date_from: dateFrom,
        date_to: dateTo
      }
    })
    
    return response.data
  } catch (error) {
    throw error
  }
}
