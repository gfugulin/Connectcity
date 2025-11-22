import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import RoutesPage from './pages/Routes';
import RouteDetail from './pages/RouteDetail';
import Favorites from './pages/Favorites';
import ActiveNavigation from './pages/ActiveNavigation';
import Profile from './pages/Profile';
import FAQ from './pages/FAQ';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/routes" element={<RoutesPage />} />
        <Route path="/route/:id" element={<RouteDetail />} />
        <Route path="/navigation" element={<ActiveNavigation />} />
        <Route path="/favorites" element={<Favorites />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/faq" element={<FAQ />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

