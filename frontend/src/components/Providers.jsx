import React, { useState, useEffect } from 'react'

function Providers() {
  const [currentProvider, setCurrentProvider] = useState('')
  const [availableProviders, setAvailableProviders] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    loadProvider()
  }, [])

  const loadProvider = async () => {
    try {
      const paymentServiceUrl = import.meta.env.VITE_PAYMENT_SERVICE_URL || 'http://localhost:8002'
      const response = await fetch(`${paymentServiceUrl}/api/v1/provider`)
      
      if (!response.ok) {
        throw new Error('Не удалось загрузить информацию о провайдере')
      }
      
      const data = await response.json()
      setCurrentProvider(data.current_provider)
      setAvailableProviders(data.available_providers)
    } catch (err) {
      setError(err.message || 'Ошибка при загрузке провайдера')
    }
  }

  const handleProviderChange = async (providerName) => {
    setLoading(true)
    setError(null)
    setSuccess(false)

    try {
      const paymentServiceUrl = import.meta.env.VITE_PAYMENT_SERVICE_URL || 'http://localhost:8002'
      const response = await fetch(`${paymentServiceUrl}/api/v1/provider`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ provider: providerName }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Не удалось изменить провайдер')
      }

      const data = await response.json()
      setCurrentProvider(data.current_provider)
      setSuccess(true)
      
      setTimeout(() => {
        setSuccess(false)
      }, 3000)
    } catch (err) {
      setError(err.message || 'Ошибка при изменении провайдера')
    } finally {
      setLoading(false)
    }
  }

  const getProviderDescription = (key) => {
    return availableProviders[key] || key
  }

  const providerKeys = Object.keys(availableProviders)

  return (
    <div>
      <h1>Управление Mock Провайдерами</h1>

      <div className="card">
        <h2>Текущий провайдер</h2>
        {currentProvider && (
          <div className="result">
            <div className="result-item">
              <label>Активный провайдер:</label>
              <span>
                <span className={`status-badge ${currentProvider === 'mock_success' ? 'status-succeeded' : currentProvider === 'mock_failed' ? 'status-failed' : 'status-pending'}`}>
                  {currentProvider}
                </span>
              </span>
            </div>
            <div className="result-item">
              <label>Описание:</label>
              <span>{getProviderDescription(currentProvider)}</span>
            </div>
          </div>
        )}

        {error && <div className="error">{error}</div>}
        {success && <div className="success">Провайдер успешно изменен!</div>}
      </div>

      <div className="card">
        <h2>Доступные провайдеры</h2>
        <div style={{ display: 'grid', gap: '1rem' }}>
          {providerKeys.map((providerKey) => (
            <div
              key={providerKey}
              style={{
                padding: '1.25rem',
                border: `2px solid ${currentProvider === providerKey ? 'var(--primary-color)' : 'var(--border-color)'}`,
                borderRadius: '0.5rem',
                backgroundColor: currentProvider === providerKey ? 'var(--secondary-color)' : 'var(--background)',
                transition: 'all 0.2s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: 'var(--text-color)' }}>
                    {providerKey}
                  </h3>
                  <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9375rem' }}>
                    {getProviderDescription(providerKey)}
                  </p>
                </div>
                <button
                  className="btn btn-primary"
                  onClick={() => handleProviderChange(providerKey)}
                  disabled={loading || currentProvider === providerKey}
                  style={{
                    minWidth: '120px',
                    opacity: currentProvider === providerKey ? 0.6 : 1,
                    cursor: currentProvider === providerKey ? 'not-allowed' : 'pointer',
                  }}
                >
                  {loading && currentProvider !== providerKey ? 'Изменение...' : currentProvider === providerKey ? 'Активен' : 'Выбрать'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h2>Информация</h2>
        <div className="result">
          <div className="result-item">
            <label>Назначение:</label>
            <span>
              Mock провайдеры используются для тестирования различных сценариев обработки платежей в локальной среде разработки.
            </span>
          </div>
          <div className="result-item">
            <label>Примечание:</label>
            <span>
              Изменения провайдера применяются немедленно и влияют на все новые платежи. 
              Управление провайдерами доступно только в локальной среде (ENVIRONMENT=local).
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Providers
