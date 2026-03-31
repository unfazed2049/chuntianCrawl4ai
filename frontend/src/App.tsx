import { Layout } from '@arco-design/web-react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import Competitors from './pages/Competitors';
import IndustryNews from './pages/IndustryNews';
import TradeShows from './pages/TradeShows';
import '@arco-design/web-react/dist/css/arco.css';
import './App.css';

const { Content } = Layout;

function App() {
  return (
    <BrowserRouter>
      <Layout className="app-layout">
        <Header />
        <Layout>
          <Sidebar />
          <Content className="app-content">
            <Routes>
              <Route path="/" element={<Navigate to="/competitors" replace />} />
              <Route path="/competitors" element={<Competitors />} />
              <Route path="/industry-news" element={<IndustryNews />} />
              <Route path="/trade-shows" element={<TradeShows />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
