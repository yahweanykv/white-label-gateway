import React, { useState } from 'react'
import { createPayment } from '../api/payments'

function PaymentForm() {
  const [formData, setFormData] = useState({
    apiKey: '',
    amount: '',
    currency: 'RUB',
    description: '',
    payment_method: 'card'
  })
  const [paymentResult, setPaymentResult] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setPaymentResult(null)
    setLoading(true)

    try {
      const result = await createPayment(formData.apiKey, {
        amount: formData.amount,
        currency: formData.currency,
        description: formData.description,
        payment_method: formData.payment_method
      })
      setPaymentResult(result)
      
      // Если требуется 3DS аутентификация, автоматически открываем страницу
      if (result.requires_action && result.next_action_url) {
        const gatewayUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
        const fullUrl = result.next_action_url.startsWith('http') 
          ? result.next_action_url 
          : `${gatewayUrl}${result.next_action_url}`
        
        // Открываем 3DS страницу в новом окне
        window.open(fullUrl, '_blank', 'width=500,height=600')
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Ошибка при создании платежа')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const getStatusBadgeClass = (status) => {
    const statusMap = {
      'succeeded': 'status-succeeded',
      'pending': 'status-pending',
      'processing': 'status-processing',
      'failed': 'status-failed',
      'requires_action': 'status-requires_action',
    }
    return statusMap[status] || 'status-pending'
  }

  return (
    <div>
      <h1>Форма Оплаты</h1>

      <div className="card">
        <h2>Создать платеж</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="apiKey">API-ключ</label>
            <input
              type="text"
              id="apiKey"
              name="apiKey"
              value={formData.apiKey}
              onChange={handleChange}
              required
              placeholder="Введите API-ключ магазина"
            />
          </div>

          <div className="form-group">
            <label htmlFor="amount">Сумма платежа</label>
            <input
              type="number"
              id="amount"
              name="amount"
              value={formData.amount}
              onChange={handleChange}
              required
              min="0.01"
              step="0.01"
              placeholder="100.00"
            />
          </div>

          <div className="form-group">
            <label htmlFor="currency">Валюта</label>
            <select
              id="currency"
              name="currency"
              value={formData.currency}
              onChange={handleChange}
              required
            >
              <option value="RUB">RUB (Российский рубль)</option>
              <option value="USD">USD (Доллар США)</option>
              <option value="EUR">EUR (Евро)</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="payment_method">Метод оплаты</label>
            <select
              id="payment_method"
              name="payment_method"
              value={formData.payment_method}
              onChange={handleChange}
              required
            >
              <option value="card">Карта</option>
              <option value="bank_transfer">Банковский перевод</option>
              <option value="digital_wallet">Цифровой кошелек</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="description">Описание платежа</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows="3"
              placeholder="Оплата заказа #123"
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Создание...' : 'Создать платеж'}
          </button>
        </form>

        {error && <div className="error">{error}</div>}

        {paymentResult && (
          <div className="result">
            <h3>Платеж успешно создан!</h3>
            <div className="result-item">
              <label>Payment ID:</label>
              <span>{paymentResult.payment_id}</span>
            </div>
            <div className="result-item">
              <label>Merchant ID:</label>
              <span>{paymentResult.merchant_id}</span>
            </div>
            <div className="result-item">
              <label>Сумма:</label>
              <span>{paymentResult.amount} {paymentResult.currency}</span>
            </div>
            <div className="result-item">
              <label>Статус:</label>
              <span>
                <span className={`status-badge ${getStatusBadgeClass(paymentResult.status)}`}>
                  {paymentResult.status}
                </span>
              </span>
            </div>
            {paymentResult.payment_method && (
              <div className="result-item">
                <label>Метод оплаты:</label>
                <span>{paymentResult.payment_method}</span>
              </div>
            )}
            {paymentResult.transaction_id && (
              <div className="result-item">
                <label>Transaction ID:</label>
                <span>{paymentResult.transaction_id}</span>
              </div>
            )}
            {paymentResult.description && (
              <div className="result-item">
                <label>Описание:</label>
                <span>{paymentResult.description}</span>
              </div>
            )}
            {paymentResult.requires_action && (
              <div className="result-item">
                <label>Требуется действие:</label>
                <span>
                  Да - требуется 3DS аутентификация
                  {paymentResult.next_action_url && (
                    <div style={{ marginTop: '0.5rem' }}>
                      <a
                        href={paymentResult.next_action_url.startsWith('http') 
                          ? paymentResult.next_action_url 
                          : `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${paymentResult.next_action_url}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="dashboard-link"
                        style={{ display: 'inline-block', marginTop: '0.5rem' }}
                      >
                        Открыть страницу 3DS →
                      </a>
                    </div>
                  )}
                </span>
              </div>
            )}
            <div className="result-item">
              <label>Дата создания:</label>
              <span>{new Date(paymentResult.created_at).toLocaleString('ru-RU')}</span>
            </div>
            {paymentResult.metadata && Object.keys(paymentResult.metadata).length > 0 && (
              <div className="result-item">
                <label>Метаданные:</label>
                <span>{JSON.stringify(paymentResult.metadata, null, 2)}</span>
              </div>
            )}
            <div className="result-item" style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)' }}>
              <label>Ссылка на платеж:</label>
              <a
                href={`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/v1/payments/${paymentResult.payment_id}?api_key=${encodeURIComponent(formData.apiKey)}`}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'inline-block',
                  color: 'var(--primary-color)',
                  textDecoration: 'none',
                  fontWeight: 600,
                  padding: '0.5rem 1rem',
                  background: 'white',
                  border: '2px solid var(--primary-color)',
                  borderRadius: '0.375rem',
                  marginTop: '0.5rem',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = 'var(--primary-color)'
                  e.target.style.color = 'white'
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = 'white'
                  e.target.style.color = 'var(--primary-color)'
                }}
              >
                Открыть платеж →
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PaymentForm
