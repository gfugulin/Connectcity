import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import RoutesPage from './pages/Routes';
import RouteDetail from './pages/RouteDetail';
import Favorites from './pages/Favorites';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/routes" element={<RoutesPage />} />
        <Route path="/route/:id" element={<RouteDetail />} />
        <Route path="/favorites" element={<Favorites />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

