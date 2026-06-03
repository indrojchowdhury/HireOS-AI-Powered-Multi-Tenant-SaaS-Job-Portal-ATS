import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/apiClient';

function Jobs() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [locationFilter, setLocationFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');

  const normalizeText = (text) => text?.toString().toLowerCase() || '';
  const formatJobType = (value) => value?.toString().replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase()) || 'Full Time';

  const jobTypes = useMemo(() => {
    const types = new Set();
    jobs.forEach((job) => {
      if (job.job_type) {
        types.add(formatJobType(job.job_type));
      }
    });
    return ['All', ...Array.from(types).sort()];
  }, [jobs]);

  const locations = useMemo(() => {
    const setLocations = new Set();
    jobs.forEach((job) => {
      setLocations.add(job.location || 'Remote');
    });
    return ['All', ...Array.from(setLocations).sort()];
  }, [jobs]);

  const filteredJobs = useMemo(() => {
    const search = normalizeText(searchTerm);
    return jobs.filter((job) => {
      const title = normalizeText(job.title);
      const company = normalizeText(job.company_name);
      const description = normalizeText(job.description);
      const location = normalizeText(job.location || 'Remote');
      const jobType = normalizeText(formatJobType(job.job_type));

      const matchesSearch =
        !search ||
        title.includes(search) ||
        company.includes(search) ||
        description.includes(search) ||
        location.includes(search);

      const matchesLocation =
        locationFilter === 'All' || location === normalizeText(locationFilter);

      const matchesType =
        typeFilter === 'All' || jobType === normalizeText(typeFilter);

      return matchesSearch && matchesLocation && matchesType;
    });
  }, [jobs, searchTerm, locationFilter, typeFilter]);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await apiClient.get('/api/jobs/');
        setJobs(Array.isArray(response.data) ? response.data : response.data.results || []);
      } catch (err) {
        console.error("Failed to load jobs:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchJobs();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-10">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6 rounded-3xl bg-gradient-to-r from-slate-900 via-brand-primary to-slate-800 p-6 shadow-sm">
          <div className="sm:flex sm:items-center sm:justify-between gap-6">
            <div>
              <h1 className="text-3xl font-extrabold text-white">Find your dream job</h1>
              <p className="text-slate-100 mt-2 max-w-2xl">
                Search the latest opportunities and filter by location or job type to match your preferences.
              </p>
            </div>
            <div className="text-sm text-slate-200">
              {loading ? 'Loading jobs…' : `${filteredJobs.length} job${filteredJobs.length === 1 ? '' : 's'} available`}
            </div>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-[1.8fr_1fr_1fr]">
            <label className="block">
              <span className="sr-only">Search jobs</span>
              <input
                type="search"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by title, company, or location"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-700 focus:border-brand-secondary focus:outline-none focus:ring-2 focus:ring-brand-secondary/20"
              />
            </label>
            <label className="block">
              <span className="sr-only">Filter by location</span>
              <select
                value={locationFilter}
                onChange={(e) => setLocationFilter(e.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-700 focus:border-brand-secondary focus:outline-none focus:ring-2 focus:ring-brand-secondary/20"
              >
                {locations.map((location) => (
                  <option key={location} value={location}>
                    {location}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="sr-only">Filter by job type</span>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-700 focus:border-brand-secondary focus:outline-none focus:ring-2 focus:ring-brand-secondary/20"
              >
                {jobTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        {loading ? (
          <p className="text-slate-500">Loading jobs...</p>
        ) : jobs.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-400">
            No jobs are available right now.
          </div>
        ) : filteredJobs.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-500">
            No jobs match your search and filters. Try broadening your criteria.
          </div>
        ) : (
          <div className="space-y-4">
            {filteredJobs.map((job) => (
              <div key={job.id} className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-bold text-slate-800">{job.title}</h2>
                    <p className="text-sm text-slate-500 mt-1">{job.company_name || 'Company not specified'}</p>
                    <p className="text-sm text-slate-600 mt-3">{job.description}</p>
                    <div className="flex flex-wrap gap-2 mt-4">
                      <span className="text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded">{job.salary_range || 'Negotiable'}</span>
                      <span className="text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded">{job.location || 'Location not specified'}</span>
                      <span className="text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded">{job.job_type?.replace('_', ' ') || 'FULL TIME'}</span>
                    </div>
                  </div>
                  <Link
                    to="/candidate-dashboard"
                    className="px-4 py-2 bg-brand-primary text-white text-sm font-semibold rounded-xl hover:bg-brand-secondary text-center"
                  >
                    Apply
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Jobs;
