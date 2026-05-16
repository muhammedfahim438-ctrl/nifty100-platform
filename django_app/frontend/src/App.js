// B100 Intelligence — Main App
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import HomePage from './pages/HomePage';
import CompaniesPage from './pages/CompaniesPage';
import CompanyDetailPage from './pages/company/CompanyDetailPage';
import ScreenerPage from './pages/ScreenerPage';
import ComparePage from './pages/ComparePage';
import SectorsPage from './pages/SectorsPage';
import HealthScoresPage from './pages/HealthScoresPage';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/"                  element={<HomePage />}          />
          <Route path="/companies"         element={<CompaniesPage />}     />
          <Route path="/company/:symbol"   element={<CompanyDetailPage />} />
          <Route path="/screener"          element={<ScreenerPage />}      />
          <Route path="/compare"           element={<ComparePage />}       />
          <Route path="/sectors"           element={<SectorsPage />}       />
          <Route path="/scores"            element={<HealthScoresPage />}  />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;