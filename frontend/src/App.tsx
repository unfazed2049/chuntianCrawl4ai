import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import Competitors from './pages/Competitors';
import IndustryNews from './pages/IndustryNews';
import TradeShows from './pages/TradeShows';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Header />
        <div className="app-shell">
          <Sidebar />
          <main className="app-content">
            <Routes>
              <Route path="/" element={<Navigate to="/competitors" replace />} />
              <Route path="/competitors" element={<Competitors />} />
              <Route path="/industry-news" element={<IndustryNews />} />
              <Route path="/trade-shows" element={<TradeShows />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
