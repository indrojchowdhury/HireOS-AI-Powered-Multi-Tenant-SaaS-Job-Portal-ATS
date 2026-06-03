import { useContext, useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

function Navbar() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);

  const dashboardPath = user?.role === 'EMPLOYER' ? '/employer-dashboard' : '/candidate-dashboard';
  const linkClass = ({ isActive }) =>
    isActive
      ? 'text-brand-primary font-bold'
      : 'text-slate-600 hover:text-brand-primary transition-colors';
  const mobileLinkClass = ({ isActive }) =>
    isActive
      ? 'block text-brand-primary font-bold'
      : 'block text-slate-600';

  const handleLogout = () => {
    logout();
    setIsOpen(false);
    navigate('/login');
  };

  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="text-2xl font-extrabold text-brand-primary tracking-tight">
            HireOS
          </Link>

          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden px-3 py-2 rounded-lg border border-slate-200 text-slate-700"
            aria-label="Toggle navigation"
          >
            Menu
          </button>

          <div className="hidden md:flex items-center gap-6 text-sm font-semibold">
            <NavLink to="/" className={linkClass}>
              Home
            </NavLink>
            <NavLink to="/jobs" className={linkClass}>
              Jobs
            </NavLink>

            {!user ? (
              <>
                <NavLink to="/login" className={linkClass}>
                  Login
                </NavLink>
                <NavLink to="/register" className={linkClass}>
                  Register
                </NavLink>
              </>
            ) : (
              <>
                {user.role === 'CANDIDATE' && (
                  <NavLink to="/subscription" className={linkClass}>
                    Subscription
                  </NavLink>
                )}
                <NavLink to={dashboardPath} className={linkClass}>
                  Dashboard
                </NavLink>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="px-4 py-2 bg-rose-50 text-rose-600 rounded-xl hover:bg-rose-100 transition-colors"
                >
                  Logout
                </button>
              </>
            )}
          </div>
        </div>

        {isOpen && (
          <div className="md:hidden border-t border-slate-100 py-4 space-y-3 text-sm font-semibold">
            <NavLink onClick={() => setIsOpen(false)} to="/" className={mobileLinkClass}>
              Home
            </NavLink>
            <NavLink onClick={() => setIsOpen(false)} to="/jobs" className={mobileLinkClass}>
              Jobs
            </NavLink>

            {!user ? (
              <>
                <NavLink onClick={() => setIsOpen(false)} to="/login" className={mobileLinkClass}>
                  Login
                </NavLink>
                <NavLink onClick={() => setIsOpen(false)} to="/register" className={mobileLinkClass}>
                  Register
                </NavLink>
              </>
            ) : (
              <>
                {user.role === 'CANDIDATE' && (
                  <NavLink onClick={() => setIsOpen(false)} to="/subscription" className={mobileLinkClass}>
                    Subscription
                  </NavLink>
                )}
                <NavLink onClick={() => setIsOpen(false)} to={dashboardPath} className={mobileLinkClass}>
                  Dashboard
                </NavLink>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="block text-left text-rose-600"
                >
                  Logout
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
