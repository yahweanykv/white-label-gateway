import React, { useState } from 'react'
import { createMerchant, getDashboard } from '../api/merchants'

function MerchantPanel() {
  const [merchantName, setMerchantName] = useState('')
  const [createdMerchant, setCreatedMerchant] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const [dashboardApiKey, setDashboardApiKey] = useState('')
  const [dashboardData, setDashboardData] = useState(null)
  const [dashboardError, setDashboardError] = useState(null)
  const [dashboardLoading, setDashboardLoading] = useState(false)

  // Состояния для логотипа при создании мерчанта
  const [createLogoFile, setCreateLogoFile] = useState(null)
  const [createLogoPreview, setCreateLogoPreview] = useState(null)
  const [createLogoUrl, setCreateLogoUrl] = useState('')

  const handleCreateLogoFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      // Проверяем тип файла
      if (!file.type.startsWith('image/')) {
        setError('Пожалуйста, выберите изображение')
        return
      }
      
      // Проверяем размер файла (макс 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError('Размер файла не должен превышать 5MB')
        return
      }

      setCreateLogoFile(file)
      setError(null)

      // Создаем preview и base64
      const reader = new FileReader()
      reader.onloadend = () => {
        setCreateLogoPreview(reader.result)
        setCreateLogoUrl(reader.result) // Используем base64 для загрузки
      }
      reader.readAsDataURL(file)
    }
  }

  const handleCreateLogoUrlChange = (e) => {
    setCreateLogoUrl(e.target.value)
    setCreateLogoFile(null)
    setCreateLogoPreview(null)
    setError(null)
  }

  const handleCreateMerchant = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const merchantData = {
        name: merchantName,
        logo_url: createLogoUrl || null
      }
      const result = await createMerchant(merchantData)
      setCreatedMerchant(result)
      // Автоматически заполняем поле для дашборда первым API ключом
      if (result.api_keys && result.api_keys.length > 0) {
        setDashboardApiKey(result.api_keys[0])
      }
      // Очищаем форму
      setMerchantName('')
      setCreateLogoFile(null)
      setCreateLogoPreview(null)
      setCreateLogoUrl('')
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Ошибка при создании магазина')
    } finally {
      setLoading(false)
    }
  }

  const handleGetDashboard = async (e) => {
    e.preventDefault()
    setDashboardError(null)
    setDashboardLoading(true)

    try {
      const result = await getDashboard(dashboardApiKey)
      setDashboardData(result)
    } catch (err) {
      setDashboardError(err.response?.data?.detail || err.message || 'Ошибка при получении дашборда')
    } finally {
      setDashboardLoading(false)
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Скопировано в буфер обмена!')
    }).catch(() => {
      alert('Не удалось скопировать')
    })
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
      <h1>Панель Мерчанта</h1>

      {/* Форма создания магазина */}
      <div className="card">
        <h2>Создать магазин</h2>
        <form onSubmit={handleCreateMerchant}>
          <div className="form-group">
            <label htmlFor="merchantName">Название магазина</label>
            <input
              type="text"
              id="merchantName"
              value={merchantName}
              onChange={(e) => setMerchantName(e.target.value)}
              required
              placeholder="Введите название магазина"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="createLogoFile">Логотип магазина (опционально)</label>
            <input
              type="file"
              id="createLogoFile"
              accept="image/*"
              onChange={handleCreateLogoFileChange}
              style={{ marginBottom: '1rem' }}
            />
            {createLogoPreview && (
              <div style={{ marginBottom: '1rem', marginTop: '0.75rem' }}>
                <label style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem', display: 'block' }}>Предпросмотр:</label>
                <img 
                  src={createLogoPreview} 
                  alt="Preview" 
                  style={{ 
                    maxWidth: '150px', 
                    maxHeight: '150px', 
                    borderRadius: '0.375rem',
                    border: '1px solid var(--border-color)',
                    display: 'block',
                    padding: '0.5rem',
                    background: 'var(--background-alt)'
                  }} 
                />
              </div>
            )}
          </div>
          
          <div className="form-group">
            <label htmlFor="createLogoUrl">Или введите URL логотипа</label>
            <input
              type="url"
              id="createLogoUrl"
              value={createLogoUrl}
              onChange={handleCreateLogoUrlChange}
              placeholder="https://example.com/logo.png"
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Создание...' : 'Создать магазин'}
          </button>
        </form>

        {error && <div className="error">{error}</div>}

        {createdMerchant && (
          <div className="result">
            <h3>Магазин успешно создан!</h3>
            <div className="result-item">
              <label>ID магазина:</label>
              <span>{createdMerchant.id}</span>
            </div>
            <div className="result-item">
              <label>Название:</label>
              <span>{createdMerchant.name}</span>
            </div>
            <div className="result-item">
              <label>API-ключ:</label>
              {createdMerchant.api_keys && createdMerchant.api_keys.length > 0 ? (
                <div
                  className="api-key"
                  onClick={() => copyToClipboard(createdMerchant.api_keys[0])}
                  title="Нажмите, чтобы скопировать"
                >
                  {createdMerchant.api_keys[0]}
                </div>
              ) : (
                <span>API-ключ не найден</span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Панель дашборда */}
      <div className="card">
        <h2>Просмотр дашборда</h2>
        <form onSubmit={handleGetDashboard}>
          <div className="form-group">
            <label htmlFor="dashboardApiKey">API-ключ</label>
            <input
              type="text"
              id="dashboardApiKey"
              value={dashboardApiKey}
              onChange={(e) => setDashboardApiKey(e.target.value)}
              required
              placeholder="Вставьте API-ключ магазина"
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={dashboardLoading}>
            {dashboardLoading ? 'Загрузка...' : 'Показать дашборд'}
          </button>
        </form>

        {dashboardError && <div className="error">{dashboardError}</div>}

        {dashboardData && (
          <div className="result">
            <h3>Информация о мерчанте</h3>
            <div className="result-item">
              <label>Merchant ID:</label>
              <span>{dashboardData.merchant.id}</span>
            </div>
            <div className="result-item">
              <label>Название:</label>
              <span>{dashboardData.merchant.name}</span>
            </div>
            {dashboardData.merchant.logo_url && (
              <div className="result-item">
                <label>Текущий логотип:</label>
                <img 
                  src={dashboardData.merchant.logo_url} 
                  alt="Logo" 
                  style={{ 
                    maxWidth: '150px', 
                    maxHeight: '150px', 
                    marginTop: '0.5rem',
                    borderRadius: '0.375rem',
                    border: '1px solid var(--border-color)',
                    padding: '0.5rem',
                    background: 'var(--background)',
                    display: 'block'
                  }} 
                />
              </div>
            )}
            <div className="result-item" style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '2px solid var(--border-color)' }}>
              <label>Ссылка на дашборд:</label>
              <a
                href={`${import.meta.env.VITE_MERCHANT_SERVICE_URL || 'http://localhost:8001'}/api/v1/dashboard?api_key=${encodeURIComponent(dashboardApiKey)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="dashboard-link"
              >
                Открыть дашборд →
              </a>
            </div>

            <h3 style={{ marginTop: '2rem' }}>Транзакции</h3>
            {dashboardData.payments && dashboardData.payments.length > 0 ? (
              <table className="table">
                <thead>
                  <tr>
                    <th>ID транзакции</th>
                    <th>Сумма</th>
                    <th>Валюта</th>
                    <th>Статус</th>
                    <th>Дата создания</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboardData.payments.map((payment) => (
                    <tr key={payment.payment_id}>
                      <td>{payment.payment_id}</td>
                      <td>{payment.amount}</td>
                      <td>{payment.currency}</td>
                      <td>
                        <span className={`status-badge ${getStatusBadgeClass(payment.status)}`}>
                          {payment.status}
                        </span>
                      </td>
                      <td>{new Date(payment.created_at).toLocaleString('ru-RU')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p style={{ color: 'var(--text-muted)', marginTop: '1rem', fontStyle: 'italic' }}>Транзакций пока нет</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default MerchantPanel
