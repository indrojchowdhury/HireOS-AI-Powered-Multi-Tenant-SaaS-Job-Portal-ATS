import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import apiClient from '../api/apiClient';

function Register() {
  // Toggle between 'CANDIDATE' and 'EMPLOYER' roles dynamically
  const [role, setRole] = useState('CANDIDATE');
  const [username, setUsername] = useState('');
  const [firstName, setFirstName] = useState(''); // First Name state
  const [lastName, setLastName] = useState('');   // Added Last Name state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  // Role-specific extra fields matching our custom Django models
  const [companyName, setCompanyName] = useState('');
  const [skills, setSkills] = useState('');
  
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Construct the payload structure explicitly matching Django serializer fields.
    const payload =
      role === 'EMPLOYER'
        ? {
            first_name: firstName,
            last_name: lastName,
            email,
            password,
            company_name: companyName,
          }
        : {
            first_name: firstName,
            last_name: lastName, // Sending last_name to backend
            email,
            password,
            role,
          };

    try {
      // Dynamically select the endpoint based on the active role tab
      const endpoint =
        role === 'EMPLOYER'
          ? '/api/auth/register-employer/'
          : '/api/auth/register/';
      
      await apiClient.post(endpoint, payload);
      setSuccess(true);
      
      // Automatically redirect to login page after 2 seconds on success
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      const backendErrors = err.response?.data;
      if (backendErrors && typeof backendErrors === 'object') {
        const errorMessages = Object.entries(backendErrors).map(
          ([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`
        );
        setError(errorMessages.join(' | '));
      } else if (typeof backendErrors === 'string') {
        setError(backendErrors);
      } else {
        setError(
          err.response?.statusText || err.message || 'Registration failed. Please check your network connection.'
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-brand-light px-4 py-8">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-slate-100">
        <div className="text-center mb-6">
          <h2 className="text-3xl font-extrabold text-brand-primary tracking-tight">Create Account</h2>
          <p className="text-slate-500 text-sm mt-2">Join HireOS recruitment network today</p>
        </div>

        {/* Role Selection Tabs */}
        <div className="flex bg-slate-100 p-1 rounded-xl mb-6">
          <button
            type="button"
            onClick={() => setRole('CANDIDATE')}
            className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${
              role === 'CANDIDATE'
                ? 'bg-white text-brand-primary shadow-sm'
                : 'text-slate-500 hover:text-brand-dark'
            }`}
          >
            Candidate
          </button>
          <button
            type="button"
            onClick={() => setRole('EMPLOYER')}
            className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${
              role === 'EMPLOYER'
                ? 'bg-white text-brand-secondary shadow-sm'
                : 'text-slate-500 hover:text-brand-dark'
            }`}
          >
            Employer
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm rounded-lg">
            Account created successfully! Redirecting to login...
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* First Name & Last Name in a side-by-side layout */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-brand-dark mb-1">First Name</label>
              <input
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-brand-dark focus:outline-none focus:ring-2 focus:ring-brand-secondary/20 focus:border-brand-secondary transition-all"
                placeholder="John"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-brand-dark mb-1">Last Name</label>
              <input
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-brand-dark focus:outline-none focus:ring-2 focus:ring-brand-secondary/20 focus:border-brand-secondary transition-all"
                placeholder="Doe"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-brand-dark mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-brand-dark focus:outline-none focus:ring-2 focus:ring-brand-secondary/20 focus:border-brand-secondary transition-all"
                placeholder="johndoe123"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-brand-dark mb-1">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-brand-dark focus:outline-none focus:ring-2 focus:ring-brand-secondary/20 focus:border-brand-secondary transition-all"
              placeholder="john@example.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-brand-dark mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-brand-dark focus:outline-none focus:ring-2 focus:ring-brand-secondary/20 focus:border-brand-secondary transition-all"
              placeholder="••••••••"
              required
            />
          </div>

          {/* Dynamic Field Conditional Rendering */}
          {role === 'CANDIDATE' ? (
            <div>
              <label className="block text-sm font-semibold text-brand-dark mb-1">Key Skills</label>
              <input
                type="text"
                value={skills}
                onChange={(e) => setSkills(e.target.value)}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-brand-dark focus:outline-none focus:ring-2 focus:ring-brand-secondary/20 focus:border-brand-secondary transition-all"
                placeholder="Python, React, SQL (Comma separated)"
              />
            </div>
          ) : (
            <div>
              <label className="block text-sm font-semibold text-brand-dark mb-1">Company Name</label>
              <input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-brand-dark focus:outline-none focus:ring-2 focus:ring-brand-secondary/20 focus:border-brand-secondary transition-all"
                placeholder="HireOS Tech Ltd."
                required
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading || success}
            className={`w-full py-2.5 text-white font-semibold rounded-xl shadow-lg transition-all transform active:scale-[0.98] disabled:opacity-70 ${
              role === 'CANDIDATE' ? 'bg-brand-primary hover:bg-brand-secondary' : 'bg-brand-secondary hover:bg-blue-700'
            }`}
          >
            {loading ? 'Processing...' : 'Register'}
          </button>
        </form>

        <div className="text-center mt-6 text-sm text-slate-500">
          Already have an account?{' '}
          <Link to="/login" className="text-brand-secondary font-semibold hover:underline">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}

export default Register;