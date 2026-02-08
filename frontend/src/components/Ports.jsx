import React from 'react'

function Ports() {
  const ports = [
    { name: 'Gateway Service', port: 8000, description: 'Основной API Gateway для обработки платежей' },
    { name: 'Merchant Service', port: 8001, description: 'Сервис управления мерчантами' },
    { name: 'Payment Service', port: 8002, description: 'Сервис обработки платежей' },
    { name: 'Notification Service', port: 8003, description: 'Сервис уведомлений' },
    { name: 'Fraud Service', port: 8004, description: 'Сервис проверки на мошенничество' },
    { name: 'Redis', port: 6379, description: 'Кэш и очереди' },
    { name: 'RabbitMQ AMQP', port: 5672, description: 'Очередь сообщений (AMQP)' },
    { name: 'RabbitMQ Management', port: 15672, description: 'Веб-интерфейс управления RabbitMQ' },
    { name: 'pgAdmin', port: 5050, description: 'Веб-интерфейс управления базами данных' },
  ]

  const getPortUrl = (port) => {
    const baseUrl = window.location.origin.split(':').slice(0, 2).join(':')
    return `${baseUrl}:${port}`
  }

  return (
    <div>
      <h1>Порты</h1>
      <div className="card">
        <p style={{ marginBottom: '1.5rem', color: '#6B7280' }}>
          Список всех используемых портов в системе. Нажмите на ссылку для перехода к сервису.
        </p>
        <table className="table">
          <thead>
            <tr>
              <th>Сервис</th>
              <th>Порт</th>
              <th>Описание</th>
              <th>Ссылка</th>
            </tr>
          </thead>
          <tbody>
            {ports.map((item, index) => (
              <tr key={index}>
                <td>
                  <strong>{item.name}</strong>
                </td>
                <td>
                  <code style={{ 
                    background: '#F3F4F6', 
                    padding: '0.25rem 0.5rem', 
                    borderRadius: '0.25rem',
                    fontFamily: 'monospace'
                  }}>
                    {item.port}
                  </code>
                </td>
                <td>{item.description}</td>
                <td>
                  <a
                    href={getPortUrl(item.port)}
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
    </div>
  )
}

export default Ports
