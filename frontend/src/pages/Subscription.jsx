import { useEffect, useState } from 'react';
import apiClient from '../api/apiClient';

function Subscription() {
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);

  useEffect(() => {
    const fetchSubscription = async () => {
      try {
        const response = await apiClient.get('/api/subscription/status/');
        setSubscription(response.data);
      } catch (err) {
        console.error("Failed to load subscription:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchSubscription();
  }, []);

  const handleUpgrade = async () => {
    setPaying(true);

    try {
      const response = await apiClient.post('/api/payments/initiate/', { plan: 'PREMIUM' });
      window.location.href = response.data.payment_url;
    } catch (err) {
      console.error("Payment start failed:", err);
      alert(err.response?.data?.detail || 'Could not start payment. Please try again.');
      setPaying(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-10">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold text-slate-800">Candidate Subscription</h1>
          <p className="text-slate-500 mt-2">Upgrade to premium using SSLCommerz.</p>
        </div>

        {loading ? (
          <p className="text-slate-500">Loading subscription...</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <h2 className="text-xl font-bold text-slate-800">Free</h2>
              <p className="text-3xl font-black text-slate-900 mt-4">BDT 0</p>
              <p className="text-sm text-slate-500 mt-3">Browse jobs and apply with basic access.</p>
              <div className="mt-6 text-sm font-semibold text-slate-500">
                Current basic plan
              </div>
            </div>

            <div className="bg-white border-2 border-brand-primary rounded-xl p-6 shadow-sm">
              <h2 className="text-xl font-bold text-slate-800">Premium</h2>
              <p className="text-3xl font-black text-slate-900 mt-4">BDT 500</p>
              <p className="text-sm text-slate-500 mt-3">Get premium candidate tools and improved application tracking.</p>

              {subscription?.is_active ? (
                <div className="mt-6 p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-lg text-sm font-semibold">
                  Premium active until {subscription.expires_at ? new Date(subscription.expires_at).toLocaleDateString() : 'next billing date'}
                </div>
              ) : (
                <button
                  type="button"
                  onClick={handleUpgrade}
                  disabled={paying}
                  className="mt-6 w-full py-3 bg-brand-primary hover:bg-brand-secondary text-white font-bold rounded-xl disabled:opacity-60"
                >
                  {paying ? 'Opening payment...' : 'Upgrade with SSLCommerz'}
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Subscription;
