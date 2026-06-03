import { Link } from 'react-router-dom';

function Footer() {
  return (
    <footer className="bg-gradient-to-br from-slate-900 via-slate-800 to-brand-primary text-slate-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h2 className="text-xl font-extrabold text-white">HireOS</h2>
            <p className="text-sm text-slate-300 mt-2">
              AI-powered hiring platform for candidates and modern companies.
            </p>
          </div>

          <div>
            <h3 className="text-sm font-bold text-white uppercase">Contact</h3>
            <div className="mt-2 space-y-2 text-sm text-slate-300">
              <p>Email: support@hireos.com</p>
              <p>Location: Dhaka, Bangladesh</p>
            </div>
          </div>
        </div>

        <div className="border-t border-white/10 mt-6 pt-4 text-sm text-slate-300 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <span>&copy; 2026 HireOS. All rights reserved.</span>
          <span className="border-l border-slate-500 pl-3">Developed by Indro J. Chowdhury</span>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
