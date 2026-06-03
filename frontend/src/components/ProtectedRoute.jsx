import { useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

function ProtectedRoute({ children, allowedRole }) {
  const { user } = useContext(AuthContext);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRole && user.role !== allowedRole) {
    const dashboardPath = user.role === 'EMPLOYER' ? '/employer-dashboard' : '/candidate-dashboard';
    return <Navigate to={dashboardPath} replace />;
  }

  return children;
}

export default ProtectedRoute;
