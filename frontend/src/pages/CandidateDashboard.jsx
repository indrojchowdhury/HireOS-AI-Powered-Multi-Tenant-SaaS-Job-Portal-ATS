import { useContext, useEffect, useState } from 'react';
import { AuthContext } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import apiClient from '../api/apiClient';

function CandidateDashboard() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [appliedJobIds, setAppliedJobIds] = useState([]);
  const [myApplications, setMyApplications] = useState([]);
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [applicationDraft, setApplicationDraft] = useState({
    cover_letter: '',
    resume: null,
  });

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await apiClient.get('/api/jobs/');
        setJobs(Array.isArray(response.data) ? response.data : response.data.results || []);
      } catch (err) {
        console.error('Failed to fetch jobs:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchJobs();
  }, []);

  // FIX: Using /api/jobs/my-applications/ — only the user's own applications + AI score
  const fetchMyApplications = async () => {
    try {
      const response = await apiClient.get('/api/jobs/my-applications/');
      const apps = Array.isArray(response.data) ? response.data : response.data.results || [];
      setMyApplications(apps);
      setAppliedJobIds(apps.map((a) => a.job));
    } catch (err) {
      console.error('Failed to fetch applications:', err);
    }
  };

  useEffect(() => { fetchMyApplications(); }, []);

  useEffect(() => {
    const fetchSubscription = async () => {
      try {
        const response = await apiClient.get('/api/subscription/status/');
        setSubscription(response.data);
      } catch (err) {
        console.error('Failed to fetch subscription:', err);
      }
    };
    fetchSubscription();
  }, []);

  const openApplicationForm = (jobId) => {
    setSelectedJobId(jobId);
    setApplicationDraft({ cover_letter: '', resume: null });
  };

  const handleDraftChange = (e) => {
    const { name, value } = e.target;
    setApplicationDraft((prev) => ({ ...prev, [name]: value }));
  };

  const handleResumeChange = (e) => {
    const file = e.target.files?.[0] || null;
    setApplicationDraft((prev) => ({ ...prev, resume: file }));
  };

  const handleApplySubmit = async (jobId) => {
    try {
      const formData = new FormData();
      formData.append('job', jobId);
      if (applicationDraft.cover_letter) formData.append('cover_letter', applicationDraft.cover_letter);
      if (applicationDraft.resume) formData.append('resume', applicationDraft.resume);

      await apiClient.post('/api/jobs/apply/', formData);
      setMessage('Application submitted successfully! AI screening in progress...');
      setSelectedJobId(null);
      setApplicationDraft({ cover_letter: '', resume: null });
      fetchMyApplications();
      setTimeout(() => setMessage(''), 4000);
    } catch (err) {
      console.error('Job application error:', err);
      alert(
        err.response?.data?.detail ||
        err.response?.data?.non_field_errors?.[0] ||
        err.response?.data?.cover_letter?.[0] ||
        err.response?.data?.resume?.[0] ||
        'Failed to apply. Please try again.'
      );
    }
  };

  const handleLogout = () => { logout(); navigate('/login'); };

  const aiScoreColor = (score) => {
    if (score >= 70) return 'bg-emerald-500';
    if (score >= 40) return 'bg-yellow-400';
    return 'bg-rose-400';
  };

  const statusBadge = (status) => {
    const map = {
      PENDING:     { label: 'Under Review', cls: 'bg-yellow-50 text-yellow-700 border-yellow-200' },
      SHORTLISTED: { label: 'Shortlisted',  cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
      INTERVIEW:   { label: 'Interview',    cls: 'bg-blue-50 text-blue-700 border-blue-200' },
      REJECTED:    { label: 'Rejected',     cls: 'bg-rose-50 text-rose-600 border-rose-200' },
    };
    const s = map[status] || { label: status, cls: 'bg-slate-100 text-slate-600 border-slate-200' };
    return (
      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${s.cls}`}>
        {s.label}
      </span>
    );
  };

  return (
    <div className="p-8 bg-slate-50 min-h-screen font-sans">
      <div className="max-w-6xl mx-auto bg-white p-8 rounded-2xl shadow-xl border border-slate-100">

        {/* Header */}
        <div className="flex justify-between items-center border-b border-slate-100 pb-5 mb-6">
          <div>
            <span className="px-3 py-1 bg-blue-50 text-blue-600 text-xs font-bold rounded-full uppercase">
              {user?.role} Portal
            </span>
            <h1 className="text-3xl font-extrabold text-slate-800 mt-2">
              Welcome Back, {user?.first_name || 'User'}!
            </h1>
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-rose-50 hover:bg-rose-100 text-rose-600 font-semibold rounded-xl transition-all"
          >
            Sign Out
          </button>
        </div>

        {message && (
          <div className="mb-4 p-3 bg-emerald-50 text-emerald-700 rounded-xl font-medium border border-emerald-200">
            {message}
          </div>
        )}

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6 items-start">

          {/* ── LEFT ── */}
          <div className="space-y-8">

            {/* Job listings */}
            <div>
              <h3 className="font-bold text-xl text-slate-800 mb-4">Available Job Circulars</h3>

              {loading ? (
                <p className="text-slate-500">Loading live jobs...</p>
              ) : jobs.length === 0 ? (
                <div className="p-8 bg-slate-50 text-center rounded-xl text-slate-400 border border-dashed">
                  No jobs posted yet.
                </div>
              ) : (
                <div className="space-y-4">
                  {jobs.map((job) => (
                    <div
                      key={job.id}
                      className="p-5 bg-slate-50 rounded-xl border border-slate-200 hover:shadow-md transition-all"
                    >
                      <div className="flex flex-col sm:flex-row sm:justify-between gap-3">
                        <div className="min-w-0">
                          <h4 className="font-bold text-lg text-slate-800">{job.title}</h4>
                          <p className="text-slate-500 text-xs mt-0.5">{job.company_name || 'Company not specified'}</p>
                          <p className="text-slate-600 text-sm mt-2">{job.description || 'No description provided.'}</p>
                          {job.requirements && (
                            <p className="text-slate-500 text-sm mt-1">
                              <span className="font-semibold text-slate-700">Requirements:</span> {job.requirements}
                            </p>
                          )}
                          <div className="mt-3 flex flex-wrap gap-2">
                            <span className="text-xs bg-slate-200 px-2 py-1 rounded text-slate-700">{job.salary_range || 'Negotiable'}</span>
                            {job.location      && <span className="text-xs bg-slate-200 px-2 py-1 rounded text-slate-700">{job.location}</span>}
                            {job.job_type      && <span className="text-xs bg-slate-200 px-2 py-1 rounded text-slate-700">{job.job_type.replace('_', ' ')}</span>}
                            {job.location_type && <span className="text-xs bg-slate-200 px-2 py-1 rounded text-slate-700">{job.location_type}</span>}
                            {job.created_at    && <span className="text-xs bg-slate-200 px-2 py-1 rounded text-slate-700">Posted {new Date(job.created_at).toLocaleDateString()}</span>}
                          </div>
                        </div>

                        <div className="shrink-0 sm:self-start">
                          <button
                            onClick={() => openApplicationForm(job.id)}
                            disabled={appliedJobIds.includes(job.id)}
                            className={`inline-flex items-center justify-center rounded-lg font-semibold text-sm transition-all px-4 py-2 ${
                              appliedJobIds.includes(job.id)
                                ? 'bg-emerald-100 text-emerald-700 cursor-not-allowed'
                                : 'bg-blue-600 hover:bg-blue-700 text-white'
                            }`}
                          >
                            {appliedJobIds.includes(job.id) ? 'Applied' : 'Apply'}
                          </button>
                        </div>
                      </div>

                      {/* Inline application form */}
                      {selectedJobId === job.id && !appliedJobIds.includes(job.id) && (
                        <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                          <h4 className="text-sm font-semibold text-slate-800 mb-3">Complete your application</h4>
                          <div className="space-y-3">
                            <div>
                              <label className="block text-sm font-medium text-slate-700 mb-1">Cover Letter</label>
                              <textarea
                                name="cover_letter"
                                value={applicationDraft.cover_letter}
                                onChange={handleDraftChange}
                                rows={4}
                                className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700 focus:outline-blue-400"
                                placeholder="Tell the recruiter why you're a great fit..."
                              />
                            </div>
                            <div>
                              <label className="block text-sm font-medium text-slate-700 mb-1">Resume (PDF)</label>
                              <input
                                type="file"
                                accept="application/pdf"
                                onChange={handleResumeChange}
                                className="block w-full text-sm text-slate-700 file:mr-4 file:rounded-full file:border-0 file:bg-blue-600 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white"
                              />
                            </div>
                            <div className="flex flex-wrap gap-3 pt-1">
                              <button
                                type="button"
                                onClick={() => handleApplySubmit(job.id)}
                                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition-all"
                              >
                                Submit Application
                              </button>
                              <button
                                type="button"
                                onClick={() => setSelectedJobId(null)}
                                className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-all"
                              >
                                Cancel
                              </button>
                            </div>
                            <p className="text-xs text-slate-400">Resume and cover letter are optional.</p>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* ── My Applications Status Tracker ── */}
            {myApplications.length > 0 && (
              <div>
                <h3 className="font-bold text-xl text-slate-800 mb-4">My Applications</h3>
                <div className="space-y-3">
                  {myApplications.map((app) => (
                    <div
                      key={app.id}
                      className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-slate-800 text-sm">{app.job_title}</p>
                          {app.created_at && (
                            <p className="text-xs text-slate-400 mt-0.5">
                              Applied {new Date(app.created_at).toLocaleDateString()}
                            </p>
                          )}

                          {app.ai_score != null || app.ai_judgment ? (
                            <div className="mt-2">
                              <div className="flex items-center gap-2">
                                <div className="flex-1 bg-slate-100 rounded-full h-1.5">
                                  <div
                                    className={`h-1.5 rounded-full transition-all ${aiScoreColor(app.ai_score ?? 0)}`}
                                    style={{ width: `${app.ai_score ?? 0}%` }}
                                  />
                                </div>
                                <span className="text-xs font-bold text-slate-600 shrink-0">
                                  ATS Score: {app.ai_score != null ? `${app.ai_score}%` : 'N/A'}
                                </span>
                              </div>
                              {app.ai_judgment && (
                                <p className="text-xs text-slate-400 mt-1 italic leading-tight">
                                  {app.ai_judgment}
                                </p>
                              )}
                            </div>
                          ) : (
                            <p className="text-xs text-slate-400 mt-2 italic">
                                ATS screening in progress...
                            </p>
                          )}

                        </div>
                        <div className="shrink-0">
                          {statusBadge(app.status)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>

          {/* ── RIGHT: Sidebar ── */}
          <div className="space-y-4 lg:sticky lg:top-8">

            {/* Profile card */}
            <div className="p-5 bg-slate-50 rounded-2xl border border-slate-200">
              <h3 className="font-bold text-lg text-slate-700">Profile</h3>
              <p className="text-slate-400 text-xs mt-0.5">Candidate account details.</p>
              <div className="mt-4 space-y-2 text-sm text-slate-600">
                <p><span className="font-semibold text-slate-800">Name: </span>{user?.first_name || ''} {user?.last_name || ''}</p>
                <p><span className="font-semibold text-slate-800">Role: </span>{user?.role || 'CANDIDATE'}</p>
                <p><span className="font-semibold text-slate-800">Email: </span>{user?.email || 'Not available'}</p>
              </div>
            </div>

            {/* Total Applications card */}
            <div className="p-5 bg-slate-50 rounded-2xl border border-slate-200">
              <h3 className="font-bold text-lg text-slate-700">Total Applications</h3>
              <p className="mt-3 text-3xl font-black text-slate-800">{myApplications.length}</p>
              {myApplications.length > 0 && (
                <div className="mt-3 space-y-1.5">
                  {['PENDING','SHORTLISTED','INTERVIEW','REJECTED'].map((s) => {
                    const count = myApplications.filter((a) => a.status === s).length;
                    if (!count) return null;
                    return (
                      <div key={s} className="flex justify-between text-xs text-slate-500">
                        <span>{s.charAt(0) + s.slice(1).toLowerCase()}</span>
                        <span className="font-bold text-slate-700">{count}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Subscription card */}
            <div className="p-5 bg-slate-50 rounded-2xl border border-slate-200">
              <h3 className="font-bold text-lg text-slate-700">Subscription</h3>
              {subscription?.is_active ? (
                <p className="mt-3 text-emerald-700 text-sm font-semibold">Premium active</p>
              ) : (
                <>
                  <p className="text-slate-500 text-sm mt-3">Free plan</p>
                  <Link
                    to="/subscription"
                    className="inline-flex mt-3 w-full justify-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition-all"
                  >
                    Upgrade to Premium
                  </Link>
                </>
              )}
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}

export default CandidateDashboard;
