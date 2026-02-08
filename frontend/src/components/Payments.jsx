import React, { useState, useEffect } from 'react'
import { getAllPayments } from '../api/payments'

function Payments() {
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  // Устанавливаем даты по умолчанию (последние 30 дней)
  useEffect(() => {
    const today = new Date()
    const thirtyDaysAgo = new Date(today)
    thirtyDaysAgo.setDate(today.getDate() - 30)
    
    setDateTo(today.toISOString().split('T')[0])
    setDateFrom(thirtyDaysAgo.toISOString().split('T')[0])
  }, [])

  // Загружаем платежи при изменении дат
  useEffect(() => {
    if (dateFrom && dateTo) {
      loadPayments()
    }
  }, [dateFrom, dateTo])

  const loadPayments = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await getAllPayments(dateFrom, dateTo)
      setPayments(result)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Ошибка при загрузке платежей')
    } finally {
      setLoading(false)
    }
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

  const getPaymentUrl = (paymentId) => {
    const gatewayUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    return `${gatewayUrl}/v1/payments/${paymentId}`
  }

  return (
    <div>
      <h1>Платежи</h1>
      <div className="card">
        <h2>Фильтр по дате</h2>
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
          <div className="form-group" style={{ flex: '1', minWidth: '200px' }}>
            <label htmlFor="dateFrom">Дата начала</label>
            <input
              type="date"
              id="dateFrom"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>
          <div className="form-group" style={{ flex: '1', minWidth: '200px' }}>
            <label htmlFor="dateTo">Дата окончания</label>
            <input
              type="date"
              id="dateTo"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button
              type="button"
              className="btn btn-primary"
              onClick={loadPayments}
              disabled={loading || !dateFrom || !dateTo}
            >
              {loading ? 'Загрузка...' : 'Обновить'}
            </button>
          </div>
        </div>

        {error && <div className="error">{error}</div>}

        {loading && <div className="loading">Загрузка платежей...</div>}

        {!loading && !error && (
          <>
            <div style={{ marginBottom: '1rem', color: '#6B7280' }}>
              Найдено платежей: <strong>{payments.length}</strong>
            </div>
            {payments.length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Payment ID</th>
                      <th>Merchant ID</th>
                      <th>Сумма</th>
                      <th>Валюта</th>
                      <th>Статус</th>
                      <th>Метод оплаты</th>
                      <th>Дата создания</th>
                      <th>Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payments.map((payment) => (
                      <tr key={payment.payment_id}>
                        <td>
                          <code style={{ 
                            fontSize: '0.875rem',
                            background: '#F3F4F6',
                            padding: '0.25rem 0.5rem',
                            borderRadius: '0.25rem'
                          }}>
                            {payment.payment_id.substring(0, 8)}...
                          </code>
                        </td>
                        <td>
                          <code style={{ 
                            fontSize: '0.875rem',
                            background: '#F3F4F6',
                            padding: '0.25rem 0.5rem',
                            borderRadius: '0.25rem'
                          }}>
                            {payment.merchant_id.substring(0, 8)}...
                          </code>
                        </td>
                        <td>{payment.amount}</td>
                        <td>{payment.currency}</td>
                        <td>
                          <span className={`status-badge ${getStatusBadgeClass(payment.status)}`}>
                            {payment.status}
                          </span>
                        </td>
                        <td>{payment.payment_method}</td>
                        <td>{new Date(payment.created_at).toLocaleString('ru-RU')}</td>
                        <td>
                          <a
                            href={getPaymentUrl(payment.payment_id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              color: 'var(--primary-color)',
                              textDecoration: 'none',
                              fontWeight: 600,
                            }}
                            onMouseEnter={(e) => {
                              e.target.style.textDecoration = 'underline'
                            }}
                            onMouseLeave={(e) => {
                              e.target.style.textDecoration = 'none'
                            }}
                          >
                            Открыть →
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p style={{ color: '#6B7280', marginTop: '1rem' }}>Платежей не найдено</p>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default Payments
