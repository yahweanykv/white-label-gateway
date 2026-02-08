import React from 'react'

function Monitoring() {
  const monitoringServices = [
    {
      name: 'Grafana',
      port: 3000,
      description: 'Визуализация метрик и дашборды',
      defaultCredentials: 'admin / admin',
      url: 'http://localhost:3000'
    },
    {
      name: 'Prometheus',
      port: 9090,
      description: 'Сбор и хранение метрик',
      defaultCredentials: null,
      url: 'http://localhost:9090'
    },
    {
      name: 'RabbitMQ Management',
      port: 15672,
      description: 'Управление очередями сообщений',
      defaultCredentials: 'guest / guest',
      url: 'http://localhost:15672'
    }
  ]

  const logServices = [
    {
      name: 'Gateway',
      path: './logs/gateway',
      description: 'Логи API Gateway'
    },
    {
      name: 'Merchant Service',
      path: './logs/merchant-service',
      description: 'Логи сервиса мерчантов'
    },
    {
      name: 'Payment Service',
      path: './logs/payment-service',
      description: 'Логи сервиса платежей'
    },
    {
      name: 'Notification Service',
      path: './logs/notification-service',
      description: 'Логи сервиса уведомлений'
    },
    {
      name: 'Fraud Service',
      path: './logs/fraud-service',
      description: 'Логи сервиса проверки на мошенничество'
    }
  ]

  const getPortUrl = (port) => {
    const baseUrl = window.location.origin.split(':').slice(0, 2).join(':')
    return `${baseUrl}:${port}`
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Скопировано в буфер обмена!')
    }).catch(() => {
      alert('Не удалось скопировать')
    })
  }

  return (
    <div>
      <h1>Мониторинг</h1>
      
      {/* Мониторинг сервисы */}
      <div className="card">
        <h2>Сервисы мониторинга</h2>
        <p style={{ marginBottom: '1.5rem', color: '#6B7280' }}>
          Веб-интерфейсы для мониторинга системы. Нажмите на ссылку для перехода к сервису.
        </p>
        <table className="table">
          <thead>
            <tr>
              <th>Сервис</th>
              <th>Порт</th>
              <th>Описание</th>
              <th>Учетные данные</th>
              <th>Ссылка</th>
            </tr>
          </thead>
          <tbody>
            {monitoringServices.map((service, index) => (
              <tr key={index}>
                <td>
                  <strong>{service.name}</strong>
                </td>
                <td>
                  <code style={{ 
                    background: '#F3F4F6', 
                    padding: '0.25rem 0.5rem', 
                    borderRadius: '0.25rem',
                    fontFamily: 'monospace'
                  }}>
                    {service.port}
                  </code>
                </td>
                <td>{service.description}</td>
                <td>
                  {service.defaultCredentials ? (
                    <span style={{ 
                      fontSize: '0.875rem',
                      color: '#6B7280',
                      fontFamily: 'monospace'
                    }}>
                      {service.defaultCredentials}
                    </span>
                  ) : (
                    <span style={{ color: '#9CA3AF' }}>Не требуется</span>
                  )}
                </td>
                <td>
                  <a
                    href={service.url}
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

      {/* Логи */}
      <div className="card">
        <h2>Логи сервисов</h2>
        <p style={{ marginBottom: '1.5rem', color: '#6B7280' }}>
          Логи хранятся в локальной директории проекта. Для просмотра логов используйте команды Docker или откройте файлы напрямую.
        </p>
        <div style={{ marginBottom: '1rem', padding: '1rem', background: '#F3F4F6', borderRadius: '0.5rem' }}>
          <strong style={{ display: 'block', marginBottom: '0.5rem' }}>Просмотр логов через Docker:</strong>
          <code style={{ 
            display: 'block',
            padding: '0.75rem',
            background: 'white',
            borderRadius: '0.25rem',
            fontFamily: 'monospace',
            fontSize: '0.875rem',
            cursor: 'pointer',
            border: '1px solid #E5E7EB'
          }}
          onClick={() => copyToClipboard('docker-compose logs -f [service-name]')}
          title="Нажмите, чтобы скопировать"
          >
            docker-compose logs -f [service-name]
          </code>
          <p style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#6B7280' }}>
            Замените [service-name] на: gateway, merchant-service, payment-service, notification-service, fraud-service
          </p>
        </div>
        <table className="table">
          <thead>
            <tr>
              <th>Сервис</th>
              <th>Путь к логам</th>
              <th>Описание</th>
              <th>Команда Docker</th>
            </tr>
          </thead>
          <tbody>
            {logServices.map((service, index) => (
              <tr key={index}>
                <td>
                  <strong>{service.name}</strong>
                </td>
                <td>
                  <code style={{ 
                    fontSize: '0.875rem',
                    background: '#F3F4F6',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '0.25rem',
                    cursor: 'pointer'
                  }}
                  onClick={() => copyToClipboard(service.path)}
                  title="Нажмите, чтобы скопировать путь"
                  >
                    {service.path}
                  </code>
                </td>
                <td>{service.description}</td>
                <td>
                  <code style={{ 
                    fontSize: '0.875rem',
                    background: '#F3F4F6',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '0.25rem',
                    cursor: 'pointer'
                  }}
                  onClick={() => copyToClipboard(`docker-compose logs -f ${service.name.toLowerCase().replace(' ', '-')}`)}
                  title="Нажмите, чтобы скопировать команду"
                  >
                    logs -f {service.name.toLowerCase().replace(' ', '-')}
                  </code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Полезные команды */}
      <div className="card">
        <h2>Полезные команды мониторинга</h2>
        <div style={{ display: 'grid', gap: '1rem' }}>
          <div style={{ padding: '1rem', background: '#F3F4F6', borderRadius: '0.5rem' }}>
            <strong style={{ display: 'block', marginBottom: '0.5rem' }}>Просмотр всех логов:</strong>
            <code 
              style={{ 
                display: 'block',
                padding: '0.75rem',
                background: 'white',
                borderRadius: '0.25rem',
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                cursor: 'pointer',
                border: '1px solid #E5E7EB'
              }}
              onClick={() => copyToClipboard('docker-compose logs -f')}
              title="Нажмите, чтобы скопировать"
            >
              docker-compose logs -f
            </code>
          </div>
          <div style={{ padding: '1rem', background: '#F3F4F6', borderRadius: '0.5rem' }}>
            <strong style={{ display: 'block', marginBottom: '0.5rem' }}>Статус всех сервисов:</strong>
            <code 
              style={{ 
                display: 'block',
                padding: '0.75rem',
                background: 'white',
                borderRadius: '0.25rem',
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                cursor: 'pointer',
                border: '1px solid #E5E7EB'
              }}
              onClick={() => copyToClipboard('docker-compose ps')}
              title="Нажмите, чтобы скопировать"
            >
              docker-compose ps
            </code>
          </div>
          <div style={{ padding: '1rem', background: '#F3F4F6', borderRadius: '0.5rem' }}>
            <strong style={{ display: 'block', marginBottom: '0.5rem' }}>Метрики Prometheus:</strong>
            <code 
              style={{ 
                display: 'block',
                padding: '0.75rem',
                background: 'white',
                borderRadius: '0.25rem',
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                cursor: 'pointer',
                border: '1px solid #E5E7EB'
              }}
              onClick={() => copyToClipboard('http://localhost:9090/metrics')}
              title="Нажмите, чтобы скопировать"
            >
              http://localhost:9090/metrics
            </code>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Monitoring
