import { useContext, useState, useEffect, useCallback } from 'react';
import { AuthContext } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import apiClient from '../api/apiClient';

function EmployerDashboard() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [myJobs, setMyJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [csvLoading, setCsvLoading] = useState({});

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    requirements: '',
    job_type: 'FULL_TIME',
    location_type: 'ONSITE',
    location: '',
    salary_min: '',
    salary_max: '',
    currency: 'BDT'
  });
  const [message, setMessage] = useState('');

  const kanbanColumns = [
    { title: 'Applied',     status: 'PENDING' },
    { title: 'Shortlisted', status: 'SHORTLISTED' },
    { title: 'Interview',   status: 'INTERVIEW' }
  ];

  // Fetch all pages of applications (backend has pagination_class)
  const fetchAllApplications = async () => {
    let results = [];
    let url = '/api/jobs/applications/';
    while (url) {
      const res = await apiClient.get(url);
      const data = res.data;
      const page = Array.isArray(data) ? data : (data.results || []);
      results = [...results, ...page];
      url = (!Array.isArray(data) && data.next) ? data.next : null;
    }
    return results;
  };

  const fetchMyJobs = useCallback(async () => {
    try {
      const [analyticsRes, jobsRes] = await Promise.all([
        apiClient.get('/dashboard/analytics/'),
        apiClient.get('/api/jobs/')
      ]);

      const jobRows = Array.isArray(jobsRes.data)
        ? jobsRes.data
        : jobsRes.data.results || [];

      const appRows = await fetchAllApplications();

      setAnalytics(analyticsRes.data);
      setApplications(appRows);
      setMyJobs(
        analyticsRes.data?.company_name
          ? jobRows.filter((j) => j.company_name === analyticsRes.data.company_name)
          : jobRows
      );
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchMyJobs(); }, [fetchMyJobs]);

  // Post new job
  const handlePostJob = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/api/jobs/', {
        ...formData,
        salary_min: formData.salary_min || null,
        salary_max: formData.salary_max || null
      });
      setMessage('Job posted successfully!');
      setFormData({
        title: '', description: '', requirements: '',
        job_type: 'FULL_TIME', location_type: 'ONSITE',
        location: '', salary_min: '', salary_max: '', currency: 'BDT'
      });
      fetchMyJobs();
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      console.error('Failed to post job:', err);
      alert(err.response?.data?.detail || 'Failed to post job. Please verify input data.');
    }
  };

  // Kanban helpers
  const getApplicationCount     = (jobId) => applications.filter((a) => a.job === jobId).length;
  const getApplicationsByStatus = (s)     => applications.filter((a) => a.status === s);

  // Drag-and-drop status update
  const handleDragStart = (e, id) => e.dataTransfer.setData('applicationId', id);
  const handleDragOver  = (e)     => e.preventDefault();

  const handleDrop = async (e, newStatus) => {
    e.preventDefault();
    const applicationId = Number(e.dataTransfer.getData('applicationId'));
    if (!applicationId) return;

    const prev = applications;
    setApplications(prev.map((a) => a.id === applicationId ? { ...a, status: newStatus } : a));

    try {
      await apiClient.patch(`/api/jobs/applications/${applicationId}/Status/`, { status: newStatus });
      fetchMyJobs();
    } catch (err) {
      console.error('Status update failed:', err);
      setApplications(prev);
      alert(err.response?.data?.detail || 'Failed to update candidate status. Please try again.');
    }
  };

  // Quick status button handler
  const handleStatusChange = async (applicationId, newStatus) => {
    const prev = applications;
    setApplications(prev.map((a) => a.id === applicationId ? { ...a, status: newStatus } : a));

    try {
      await apiClient.patch(`/api/jobs/applications/${applicationId}/Status/`, { status: newStatus });
      fetchMyJobs();
    } catch (err) {
      console.error('Status update failed:', err);
      setApplications(prev);
      alert(err.response?.data?.detail || 'Failed to update candidate status. Please try again.');
    }
  };

  // Resume download
  const handleDownloadResume = async (applicationId, candidateName) => {
    try {
      const res = await apiClient.get(
        `/applications/${applicationId}/download-resume/`,
        { responseType: 'blob' }
      );
      const url  = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href     = url;
      link.download = `Resume_${candidateName || 'candidate'}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Resume download failed:', err);
      alert(err.response?.data?.detail || 'Failed to download resume. Please try again.');
    }
  };

  // Offer letter generation
  const handleGenerateOfferLetter = async (applicationId, candidateName) => {
    try {
      const res = await apiClient.post(
        `/api/jobs/applications/${applicationId}/offer-letter/`,
        {},
        { responseType: 'blob' }
      );
      const url  = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href     = url;
      link.download = `Offer_Letter_${candidateName || 'candidate'}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Offer letter generation failed:', err);
      alert(err.response?.data?.detail || 'Failed to generate offer letter. Please try again.');
    }
  };

  // Export candidates as CSV
  const handleExportCSV = async (jobId) => {
    setCsvLoading((p) => ({ ...p, [jobId]: true }));
    try {
      await apiClient.post(`/jobs/${jobId}/export-candidates/`);
      alert('CSV export queued! You will receive it via email shortly.');
    } catch (err) {
      console.error('CSV export failed:', err);
      alert(err.response?.data?.detail || 'Failed to queue CSV export.');
    } finally {
      setCsvLoading((p) => ({ ...p, [jobId]: false }));
    }
  };

  const handleDeleteJob = async (jobId, jobSlug) => {
    if (!window.confirm('Delete this job posting? This cannot be undone.')) return;
    try {
      await apiClient.delete(`/api/jobs/${jobSlug}/`);
      setMyJobs((prev) => prev.filter((job) => job.id !== jobId));
      setMessage('Job deleted successfully.');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      console.error('Failed to delete job:', err);
      alert(err.response?.data?.detail || 'Failed to delete job. Please try again.');
    }
  };

  const aiScoreColor = (score) => {
    if (score >= 70) return 'bg-emerald-500';
    if (score >= 40) return 'bg-yellow-400';
    return 'bg-rose-400';
  };

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <div className="p-8 bg-slate-50 min-h-screen font-sans">
      <div className="max-w-7xl mx-auto bg-white p-8 rounded-2xl shadow-xl border border-slate-100">

        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-5 mb-6">
          <div>
            <span className="px-3 py-1 bg-emerald-50 text-emerald-600 text-xs font-bold rounded-full uppercase">
              {user?.role} Suite
            </span>
            <h1 className="text-3xl font-extrabold text-slate-800 mt-2">
              Corporate Suite, {user?.first_name || 'HR'}
            </h1>
            {analytics?.company_name && (
              <p className="text-slate-500 text-sm mt-1">{analytics.company_name}</p>
            )}
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <Link
              to="/schedule-interview"
              className="inline-flex items-center justify-center rounded-xl border border-emerald-600 px-4 py-2 text-sm font-semibold text-emerald-600 hover:bg-emerald-50"
            >
              Schedule Interview
            </Link>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-rose-50 hover:bg-rose-100 text-rose-600 font-semibold rounded-xl transition-all"
            >
              Sign Out
            </button>
          </div>
        </div>

        {message && (
          <div className="mb-4 p-3 bg-emerald-50 text-emerald-700 rounded-xl font-medium border border-emerald-200">
            {message}
          </div>
        )}

        <div className="grid grid-cols-1 gap-6">

          {/* Post Job + Company Summary */}
          <div className="p-6 bg-slate-50 rounded-2xl border border-slate-200 grid grid-cols-1 xl:grid-cols-[1.7fr_1fr] gap-6">

            {/* Post Job Form */}
            <div>
              <h3 className="font-bold text-lg text-slate-800 mb-4">Post a New Job</h3>
              <form onSubmit={handlePostJob} className="space-y-4">
                <div>
                  <label className="text-xs font-bold text-slate-600 block mb-1">Job Title</label>
                  <input
                    type="text" required value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="w-full p-2 border rounded-xl bg-white text-sm focus:outline-blue-500"
                    placeholder="e.g. React Developer"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-600 block mb-1">Description</label>
                  <textarea
                    required value={formData.description} rows="3"
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full p-2 border rounded-xl bg-white text-sm focus:outline-blue-500 resize-none"
                    placeholder="Job roles and responsibilities..."
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-600 block mb-1">Requirements</label>
                  <textarea
                    required value={formData.requirements} rows="3"
                    onChange={(e) => setFormData({ ...formData, requirements: e.target.value })}
                    className="w-full p-2 border rounded-xl bg-white text-sm focus:outline-blue-500 resize-none"
                    placeholder="Experience, skills, education..."
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-bold text-slate-600 block mb-1">Job Type</label>
                    <select
                      value={formData.job_type}
                      onChange={(e) => setFormData({ ...formData, job_type: e.target.value })}
                      className="w-full p-2 border rounded-xl bg-white text-sm"
                    >
                      <option value="FULL_TIME">Full Time</option>
                      <option value="PART_TIME">Part Time</option>
                      <option value="CONTRACT">Contract</option>
                      <option value="INTERNSHIP">Internship</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-bold text-slate-600 block mb-1">Location Type</label>
                    <select
                      value={formData.location_type}
                      onChange={(e) => setFormData({ ...formData, location_type: e.target.value })}
                      className="w-full p-2 border rounded-xl bg-white text-sm"
                    >
                      <option value="ONSITE">Onsite</option>
                      <option value="REMOTE">Remote</option>
                      <option value="HYBRID">Hybrid</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-600 block mb-1">Location</label>
                  <input
                    type="text" required value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="w-full p-2 border rounded-xl bg-white text-sm focus:outline-blue-500"
                    placeholder="e.g. Remote / Dhaka"
                  />
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="text-xs font-bold text-slate-600 block mb-1">Min Salary</label>
                    <input
                      type="number" value={formData.salary_min}
                      onChange={(e) => setFormData({ ...formData, salary_min: e.target.value })}
                      className="w-full p-2 border rounded-xl bg-white text-sm"
                      placeholder="50000"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-bold text-slate-600 block mb-1">Max Salary</label>
                    <input
                      type="number" value={formData.salary_max}
                      onChange={(e) => setFormData({ ...formData, salary_max: e.target.value })}
                      className="w-full p-2 border rounded-xl bg-white text-sm"
                      placeholder="70000"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-bold text-slate-600 block mb-1">Currency</label>
                    <input
                      type="text" required value={formData.currency}
                      onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                      className="w-full p-2 border rounded-xl bg-white text-sm"
                      placeholder="BDT"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  className="w-full py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm rounded-xl transition-all"
                >
                  Publish Circular
                </button>
              </form>
            </div>

            {/* Company Summary */}
            <div className="p-6 bg-white rounded-2xl border border-slate-200">
              <h3 className="font-bold text-lg text-slate-800 mb-4">Company Summary</h3>
              <div className="grid grid-cols-1 gap-4">
                {[
                  { label: 'Total Jobs',   value: analytics?.metrics?.total_jobs         ?? myJobs.length },
                  { label: 'Applications', value: analytics?.metrics?.total_applications  ?? applications.length },
                  { label: 'Pending',      value: analytics?.application_status_counts?.PENDING     ?? 0 },
                  { label: 'Shortlisted',  value: analytics?.application_status_counts?.SHORTLISTED ?? 0 },
                  { label: 'Interview',    value: analytics?.application_status_counts?.INTERVIEW   ?? 0 },
                  { label: 'Rejected',     value: analytics?.application_status_counts?.REJECTED    ?? 0 },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                    <p className="text-xs font-bold text-slate-500 uppercase">{label}</p>
                    <p className="mt-1 text-2xl font-black text-slate-800">{value}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Candidate pipeline + Job Listings */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-xl text-slate-800">Your Active Job Postings</h3>
              <span className="bg-emerald-100 text-emerald-800 text-xs px-2.5 py-1 rounded-full font-bold">
                Total: {myJobs.length}
              </span>
            </div>

            {/* Candidate Pipeline Board */}
            <div className="mb-8">
              <h3 className="font-bold text-xl text-slate-800 mb-4">Candidate Pipeline</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {kanbanColumns.map((col) => (
                  <div
                    key={col.status}
                    onDragOver={handleDragOver}
                    onDrop={(e) => handleDrop(e, col.status)}
                    className="bg-slate-50 border border-slate-200 rounded-xl p-4 min-h-[220px]"
                  >
                    <div className="flex justify-between items-center mb-3">
                      <h4 className="font-bold text-slate-700">{col.title}</h4>
                      <span className="text-xs bg-white border border-slate-200 text-slate-500 px-2 py-1 rounded-full">
                        {getApplicationsByStatus(col.status).length}
                      </span>
                    </div>

                    <div className="space-y-3">
                      {getApplicationsByStatus(col.status).map((app) => (
                        <div
                          key={app.id}
                          draggable
                          onDragStart={(e) => handleDragStart(e, app.id)}
                          className="bg-white border border-slate-200 rounded-lg p-3 shadow-sm cursor-move"
                        >
                          {/* Candidate basic info */}
                          <p className="font-semibold text-sm text-slate-800">
                            {app.candidate_name || app.candidate_email}
                          </p>
                          <p className="text-xs text-slate-500 mt-0.5">{app.job_title}</p>
                          <p className="text-xs text-slate-400">{app.candidate_email}</p>
                          {app.created_at && (
                            <p className="text-xs text-slate-300 mt-0.5">
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

                          {/* Resume download — always visible */}
                          <button
                            type="button"
                            onClick={() => handleDownloadResume(app.id, app.candidate_name)}
                            className="mt-2 w-full bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold py-1.5 rounded-lg transition-all"
                          >
                            ↓ Download Resume
                          </button>

                          {/* PENDING: Shortlist or Reject */}
                          {app.status === 'PENDING' && (
                            <div className="mt-2 grid grid-cols-2 gap-2">
                              <button
                                type="button"
                                onClick={() => handleStatusChange(app.id, 'SHORTLISTED')}
                                className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold py-1.5 rounded-lg transition-all"
                              >
                                Shortlist
                              </button>
                              <button
                                type="button"
                                onClick={() => handleStatusChange(app.id, 'REJECTED')}
                                className="bg-rose-50 hover:bg-rose-100 text-rose-600 text-xs font-semibold py-1.5 rounded-lg transition-all"
                              >
                                Reject
                              </button>
                            </div>
                          )}

                          {/* SHORTLISTED: Move to Interview, Generate Offer Letter, or Reject */}
                          {app.status === 'SHORTLISTED' && (
                            <div className="mt-2 space-y-2">
                              <button
                                type="button"
                                onClick={() => handleStatusChange(app.id, 'INTERVIEW')}
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold py-1.5 rounded-lg transition-all"
                              >
                                Move to Interview
                              </button>
                              <button
                                type="button"
                                onClick={() => handleGenerateOfferLetter(app.id, app.candidate_name)}
                                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold py-1.5 rounded-lg transition-all"
                              >
                                Generate Offer Letter
                              </button>
                              <button
                                type="button"
                                onClick={() => handleStatusChange(app.id, 'REJECTED')}
                                className="w-full bg-rose-50 hover:bg-rose-100 text-rose-600 text-xs font-semibold py-1.5 rounded-lg transition-all"
                              >
                                Reject
                              </button>
                            </div>
                          )}

                          {/* INTERVIEW: Generate Offer Letter or Reject */}
                          {app.status === 'INTERVIEW' && (
                            <div className="mt-2 space-y-2">
                              <button
                                type="button"
                                onClick={() => handleGenerateOfferLetter(app.id, app.candidate_name)}
                                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold py-1.5 rounded-lg transition-all"
                              >
                                Generate Offer Letter
                              </button>
                              <button
                                type="button"
                                onClick={() => handleStatusChange(app.id, 'REJECTED')}
                                className="w-full bg-rose-50 hover:bg-rose-100 text-rose-600 text-xs font-semibold py-1.5 rounded-lg transition-all"
                              >
                                Reject
                              </button>
                            </div>
                          )}
                        </div>
                      ))}

                      {getApplicationsByStatus(col.status).length === 0 && (
                        <p className="text-sm text-slate-400 text-center py-8">No candidates</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Active job postings list */}
            {loading ? (
              <p className="text-slate-500">Loading your vacancies...</p>
            ) : myJobs.length === 0 ? (
              <div className="p-8 bg-slate-50 text-center rounded-xl text-slate-400 border border-dashed">
                You haven&apos;t posted any jobs yet. Use the form above!
              </div>
            ) : (
              <div className="space-y-4">
                {myJobs.map((job) => (
                  <div key={job.id} className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm">
                    <div className="flex justify-between items-start gap-4">
                      <div>
                        <h4 className="font-bold text-lg text-slate-800">{job.title}</h4>
                        <p className="text-slate-500 text-xs mt-1">
                          {job.company_name || analytics?.company_name || 'Company not specified'}
                        </p>
                        <p className="text-slate-500 text-xs mt-1">
                          {job.location || 'Not specified'} | {job.salary_range || 'Negotiable'} |{' '}
                          {job.job_type?.replace('_', ' ') || 'FULL TIME'} | {job.location_type || 'ONSITE'}
                        </p>
                      </div>
                      <div className="flex flex-col items-end gap-2 shrink-0">
                        <span className="text-xs font-bold bg-slate-100 text-slate-600 px-2 py-1 rounded whitespace-nowrap">
                          {getApplicationCount(job.id)} Applicants
                        </span>
                        <button
                          type="button"
                          onClick={() => handleExportCSV(job.id)}
                          disabled={csvLoading[job.id]}
                          className="text-xs font-semibold text-emerald-600 hover:text-emerald-800 underline disabled:opacity-50"
                        >
                          {csvLoading[job.id] ? 'Queuing...' : 'Export CSV'}
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteJob(job.id, job.slug)}
                          className="text-xs font-semibold text-rose-600 hover:text-rose-800 underline"
                        >
                          Delete Job
                        </button>
                      </div>
                    </div>
                    <p className="text-slate-600 text-sm mt-3 border-t pt-2 border-slate-100">
                      {job.description}
                    </p>
                    {job.requirements && (
                      <p className="text-slate-500 text-sm mt-2">
                        <span className="font-semibold text-slate-700">Requirements:</span> {job.requirements}
                      </p>
                    )}
                    {job.created_at && (
                      <p className="text-slate-400 text-xs mt-3">
                        Posted {new Date(job.created_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default EmployerDashboard;
