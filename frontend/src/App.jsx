import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import Jobs from './pages/Jobs';
import Login from './pages/Login';
import Register from './pages/Register';
import EmployerDashboard from './pages/EmployerDashboard';
import CandidateDashboard from './pages/CandidateDashboard';
import ScheduleInterview from './pages/ScheduleInterview';
import Subscription from './pages/Subscription';
import PaymentResult from './pages/PaymentResult';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Navbar />
        <Routes>
          {/* Default Landing Page */}
          <Route path="/" element={<Home />} />
          <Route path="/jobs" element={<Jobs />} />
          
          {/* Auth Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Role Based Dashboards */}
          <Route path="/employer-dashboard" element={
            <ProtectedRoute allowedRole="EMPLOYER">
              <EmployerDashboard />
            </ProtectedRoute>
          } />
          <Route path="/candidate-dashboard" element={
            <ProtectedRoute allowedRole="CANDIDATE">
              <CandidateDashboard />
            </ProtectedRoute>
          } />
          <Route path="/schedule-interview" element={
            <ProtectedRoute allowedRole="EMPLOYER">
              <ScheduleInterview />
            </ProtectedRoute>
          } />
          <Route path="/subscription" element={
            <ProtectedRoute allowedRole="CANDIDATE">
              <Subscription />
            </ProtectedRoute>
          } />

          {/* Payment Result Pages */}
          <Route path="/payment/success" element={<PaymentResult type="success" />} />
          <Route path="/payment/fail" element={<PaymentResult type="fail" />} />
          <Route path="/payment/cancel" element={<PaymentResult type="cancel" />} />
          
          {/* Catch-all route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Footer />
      </Router>
    </AuthProvider>
  );
}

export default App;
