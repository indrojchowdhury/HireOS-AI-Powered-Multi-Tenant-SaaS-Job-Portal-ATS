import React, { createContext, useState, useEffect } from 'react';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // initial load এ সব ডেটা রিড করা হচ্ছে
    const accessToken = localStorage.getItem('access_token');
    const username = localStorage.getItem('username');
    const role = localStorage.getItem('user_role');
    const firstName = localStorage.getItem('first_name');
    const lastName = localStorage.getItem('last_name');

    if (accessToken && role) {
      setUser({ username, role, first_name: firstName, last_name: lastName });
    }
    setLoading(false);
  }, []);

  const login = (access, refresh, userData) => {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('username', userData.username);
    localStorage.setItem('user_role', userData.role);
    localStorage.setItem('first_name', userData.first_name || '');
    localStorage.setItem('last_name', userData.last_name || '');
    
    setUser({ 
      username: userData.username, 
      role: userData.role,
      first_name: userData.first_name,
      last_name: userData.last_name
    });
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};