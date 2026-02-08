import React from 'react'
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom'
import MerchantPanel from './components/MerchantPanel'
import PaymentForm from './components/PaymentForm'
import Ports from './components/Ports'
import Payments from './components/Payments'
import Merchants from './components/Merchants'
import Monitoring from './components/Monitoring'
import Providers from './components/Providers'
import './App.css'

function App() {
  return (
    <Router>
      <div className="container">
        <nav className="nav">
          <ul>
            <li>
              <NavLink to="/" end>
                Панель Мерчанта
              </NavLink>
            </li>
            <li>
              <NavLink to="/payment-form">
                Форма Оплаты
              </NavLink>
            </li>
            <li>
              <NavLink to="/ports">
                Порты
              </NavLink>
            </li>
            <li>
              <NavLink to="/payments">
                Платежи
              </NavLink>
            </li>
            <li>
              <NavLink to="/merchants">
                Мерчанты
              </NavLink>
            </li>
            <li>
              <NavLink to="/monitoring">
                Мониторинг
              </NavLink>
            </li>
            <li>
              <NavLink to="/providers">
                Провайдеры
              </NavLink>
            </li>
          </ul>
        </nav>

        <Routes>
          <Route path="/" element={<MerchantPanel />} />
          <Route path="/payment-form" element={<PaymentForm />} />
          <Route path="/ports" element={<Ports />} />
          <Route path="/payments" element={<Payments />} />
          <Route path="/merchants" element={<Merchants />} />
          <Route path="/monitoring" element={<Monitoring />} />
          <Route path="/providers" element={<Providers />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
