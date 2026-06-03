import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/apiClient';
import heroImage from '../assets/hero.png';

function Home() {
  const [latestJobs, setLatestJobs] = useState([]);
  const [loadingJobs, setLoadingJobs] = useState(true);

  const features = [
    {
      title: 'Smart Job Matching',
      text: 'Connect candidates with roles that match their skills, goals, and experience.'
    },
    {
      title: 'AI Resume Screening',
      text: 'Help hiring teams review applications faster with consistent candidate insights.'
    },
    {
      title: 'Employer Analytics',
      text: 'Track jobs, applications, and hiring progress from a focused dashboard.'
    }
  ];

  useEffect(() => {
    const fetchLatestJobs = async () => {
      try {
        const response = await apiClient.get('/api/jobs/');
        const jobList = Array.isArray(response.data) ? response.data : response.data.results || [];
        setLatestJobs(jobList.slice(0, 3));
      } catch (err) {
        console.error("Failed to load latest jobs:", err);
      } finally {
        setLoadingJobs(false);
      }
    };

    fetchLatestJobs();
  }, []);

  return (
    <div className="bg-slate-50 min-h-screen">
      <section className="relative min-h-[320px] flex items-center bg-gradient-to-br from-slate-900 via-slate-800 to-brand-primary">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-white">
          <div className="max-w-2xl">
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight">
              Find your dream job
            </h1>
            <p className="mt-4 text-base sm:text-lg text-slate-100 leading-7 max-w-xl">
              Discover fresh openings from top employers and move faster toward your next career move.
            </p>
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-16 mt-10">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
          <div>
            <h2 className="text-2xl font-extrabold text-slate-800">Latest Jobs</h2>
            <p className="text-slate-500 mt-2">Fresh opportunities from HireOS employers.</p>
          </div>
          <Link to="/jobs" className="text-sm font-semibold text-brand-primary hover:text-brand-secondary">
            View all jobs
          </Link>
        </div>

        {loadingJobs ? (
          <p className="text-slate-500">Loading latest jobs...</p>
        ) : latestJobs.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-400">
            No jobs posted yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {latestJobs.map((job) => (
              <div key={job.id} className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                <h3 className="text-lg font-bold text-slate-800">{job.title}</h3>
                <p className="text-sm text-slate-500 mt-1">{job.company_name || 'Company not specified'}</p>
                <p className="text-sm text-slate-600 mt-3 line-clamp-3">{job.description}</p>
                <div className="flex flex-wrap gap-2 mt-4">
                  <span className="text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded">{job.salary_range || 'Negotiable'}</span>
                  <span className="text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded">{job.location || 'Remote'}</span>
                </div>
                <Link
                  to="/jobs"
                  className="inline-block mt-5 px-4 py-2 bg-brand-primary text-white text-sm font-semibold rounded-xl hover:bg-brand-secondary"
                >
                  View Job
                </Link>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {features.map((feature) => (
            <div key={feature.title} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="text-lg font-bold text-slate-800">{feature.title}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-500">{feature.text}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default Home;
