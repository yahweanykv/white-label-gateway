import React, { useState, useEffect } from 'react'
import { getAllMerchants } from '../api/merchants'

function Merchants() {
  const [merchants, setMerchants] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadMerchants()
  }, [])

  const loadMerchants = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await getAllMerchants()
      setMerchants(result)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Ошибка при загрузке мерчантов')
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Скопировано в буфер обмена!')
    }).catch(() => {
      alert('Не удалось скопировать')
    })
  }

  const getDashboardUrl = (apiKey) => {
    const merchantServiceUrl = import.meta.env.VITE_MERCHANT_SERVICE_URL || 'http://localhost:8001'
    // Используем специальный URL для дашборда с API ключом
    return `${merchantServiceUrl}/api/v1/dashboard?api_key=${encodeURIComponent(apiKey)}`
  }

  return (
    <div>
      <h1>Мерчанты</h1>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <p style={{ margin: 0, color: '#6B7280' }}>
            Список всех мерчантов в системе
          </p>
          <button
            type="button"
            className="btn btn-primary"
            onClick={loadMerchants}
            disabled={loading}
          >
            {loading ? 'Загрузка...' : 'Обновить'}
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {loading && <div className="loading">Загрузка мерчантов...</div>}

        {!loading && !error && (
          <>
            <div style={{ marginBottom: '1rem', color: '#6B7280' }}>
              Всего мерчантов: <strong>{merchants.length}</strong>
            </div>
            {merchants.length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Название</th>
                      <th>Домен</th>
                      <th>API Ключи</th>
                      <th>Статус</th>
                      <th>Дата создания</th>
                      <th>Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {merchants.map((merchant) => (
                      <tr key={merchant.id}>
                        <td>
                          <code style={{ 
                            fontSize: '0.875rem',
                            background: '#F3F4F6',
                            padding: '0.25rem 0.5rem',
                            borderRadius: '0.25rem'
                          }}>
                            {merchant.id.substring(0, 8)}...
                          </code>
                        </td>
                        <td>
                          <strong>{merchant.name}</strong>
                        </td>
                        <td>{merchant.domain || '-'}</td>
                        <td>
                          {merchant.api_keys && merchant.api_keys.length > 0 ? (
                            <div>
                              {merchant.api_keys.map((apiKey, index) => (
                                <div
                                  key={index}
                                  className="api-key"
                                  onClick={() => copyToClipboard(apiKey)}
                                  title="Нажмите, чтобы скопировать"
                                  style={{ marginBottom: '0.5rem' }}
                                >
                                  {apiKey.substring(0, 20)}...
                                </div>
                              ))}
                            </div>
                          ) : (
                            <span style={{ color: '#9CA3AF' }}>Нет API ключей</span>
                          )}
                        </td>
                        <td>
                          <span className={`status-badge ${merchant.is_active ? 'status-succeeded' : 'status-failed'}`}>
                            {merchant.is_active ? 'Активен' : 'Неактивен'}
                          </span>
                        </td>
                        <td>{new Date(merchant.created_at).toLocaleString('ru-RU')}</td>
                        <td>
                          {merchant.api_keys && merchant.api_keys.length > 0 ? (
                            <a
                              href={getDashboardUrl(merchant.api_keys[0])}
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
                              Дашборд →
                            </a>
                          ) : (
                            <span style={{ color: '#9CA3AF' }}>-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p style={{ color: '#6B7280', marginTop: '1rem' }}>Мерчантов не найдено</p>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default Merchants
