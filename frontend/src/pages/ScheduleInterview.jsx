import { useState } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/apiClient';

function ScheduleInterview() {
  const [formData, setFormData] = useState({
    title: '',
    candidate_email: '',
    date: '',
    time: '',
    duration_minutes: 30,
  });
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setResult(null);

    try {
      const response = await apiClient.post('/schedule-interview/', {
        title: formData.title,
        candidate_email: formData.candidate_email,
        date: formData.date,
        time: formData.time,
        duration_minutes: formData.duration_minutes,
      });

      setResult(response.data);
      setFormData({
        title: '',
        candidate_email: '',
        date: '',
        time: '',
        duration_minutes: 30,
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to schedule interview. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-10">
      <div className="max-w-2xl mx-auto bg-white p-8 rounded-3xl shadow-sm border border-slate-200">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900">Schedule Interview</h1>
            <p className="text-slate-500 mt-2">Create a Google Calendar interview with an automatic Meet link.</p>
          </div>
          <Link to="/employer-dashboard" className="text-sm font-semibold text-brand-primary hover:text-brand-secondary">
            Back to Dashboard
          </Link>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Interview title</span>
            <input
              name="title"
              type="text"
              value={formData.title}
              onChange={handleChange}
              placeholder="e.g. Interview with candidate"
              required
              className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-700 focus:border-brand-secondary focus:outline-none focus:ring-2 focus:ring-brand-secondary/20"
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-700">Candidate email</span>
            <input
              name="candidate_email"
              type="email"
              value={formData.candidate_email}
              onChange={handleChange}
              placeholder="candidate@example.com"
              required
              className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-700 focus:border-brand-secondary focus:outline-none focus:ring-2 focus:ring-brand-secondary/20"
            />
          </label>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label className="block">
              <span className="text-sm font-medium text-slate-700">Date</span>
              <input
                name="date"
                type="date"
                value={formData.date}
                onChange={handleChange}
                required
                className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-700 focus:border-brand-secondary focus:outline-none focus:ring-2 focus:ring-brand-secondary/20"
              />
            </label>
            <label className="block">
              <span className="text-sm font-medium text-slate-700">Time</span>
              <input
                name="time"
                type="time"
                value={formData.time}
                onChange={handleChange}
                required
                className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-700 focus:border-brand-secondary focus:outline-none focus:ring-2 focus:ring-brand-secondary/20"
              />
            </label>
          </div>

          <label className="block">
            <span className="text-sm font-medium text-slate-700">Duration (minutes)</span>
            <input
              name="duration_minutes"
              type="number"
              min="15"
              step="15"
              value={formData.duration_minutes}
              onChange={handleChange}
              className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-700 focus:border-brand-secondary focus:outline-none focus:ring-2 focus:ring-brand-secondary/20"
            />
          </label>

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-2xl bg-brand-primary px-5 py-3 text-white font-semibold shadow-sm hover:bg-brand-secondary transition-all disabled:opacity-70"
          >
            {submitting ? 'Scheduling...' : 'Create Google Meet Interview'}
          </button>
        </form>

        {error && <div className="mt-5 rounded-2xl bg-rose-50 border border-rose-100 p-4 text-sm text-rose-700">{error}</div>}

        {result && (
          <div className="mt-5 rounded-2xl bg-emerald-50 border border-emerald-100 p-4 text-sm text-emerald-800">
            <p className="font-semibold">Interview created successfully.</p>
            <p className="mt-2">Google Meet link:</p>
            <a href={result.meet_link} target="_blank" rel="noreferrer" className="text-brand-primary hover:text-brand-secondary break-all">
              {result.meet_link}
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

export default ScheduleInterview;
