import { Link, useLocation } from 'react-router-dom';

function PaymentResult({ type }) {
  const location = useLocation();
  const transactionId = new URLSearchParams(location.search).get('tran_id');

  const isSuccess = type === 'success';
  const title = isSuccess ? 'Payment Successful' : type === 'cancel' ? 'Payment Cancelled' : 'Payment Failed';
  const message = isSuccess
    ? 'Your premium subscription is now active.'
    : 'Your subscription was not activated. You can try again anytime.';

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
      <div className="bg-white border border-slate-200 rounded-xl p-8 max-w-md w-full text-center shadow-sm">
        <h1 className={`text-2xl font-extrabold ${isSuccess ? 'text-emerald-700' : 'text-rose-700'}`}>
          {title}
        </h1>
        <p className="text-slate-500 mt-3">{message}</p>
        {transactionId && (
          <p className="text-xs text-slate-400 mt-4">Transaction ID: {transactionId}</p>
        )}
        <Link
          to="/candidate-dashboard"
          className="inline-block mt-6 px-5 py-3 bg-brand-primary text-white font-semibold rounded-xl hover:bg-brand-secondary"
        >
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}

export default PaymentResult;
