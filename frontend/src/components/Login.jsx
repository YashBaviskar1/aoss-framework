import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, Github, Cpu } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    // --- Mock Login Logic ---
    // In a real app, you'd have validation and an API call here.
    console.log('Logging in with:', { email, password });
    
    // For demonstration, navigate to the chat page on successful login
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-base-100 to-blue-50 p-24">
      <div className="card w-full max-w-md bg-base-100 shadow-xl border border-base-300">
        <div className="card-body">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="inline-block p-3 bg-primary/10 rounded-2xl mb-4">
              <Cpu className="w-8 h-8 text-primary" />
            </div>
            <h1 className="text-3xl font-bold text-base-content">Welcome Back</h1>
            <p className="text-base-content/70 mt-2">
              Sign in to access the AOSS Orchestrator.
            </p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleLogin} className="space-y-4">
            {/* Email Input */}
            <div className="form-control">
              <label className="label">
                <span className="label-text text-base-content/80">Email Address</span>
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3">
                  <Mail className="w-5 h-5 text-base-content/40" />
                </span>
                <input
                  type="email"
                  placeholder="you@example.com"
                  className="input input-bordered w-full pl-10"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Password Input */}
            <div className="form-control">
              <label className="label">
                <span className="label-text text-base-content/80">Password</span>
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3">
                  <Lock className="w-5 h-5 text-base-content/40" />
                </span>
                <input
                  type="password"
                  placeholder="••••••••"
                  className="input input-bordered w-full pl-10"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <label className="label">
                <a href="#" className="label-text-alt link link-hover text-sm text-primary">
                  Forgot password?
                </a>
              </label>
            </div>

            {/* Submit Button */}
            <div className="form-control mt-6">
              <button type="submit" className="btn btn-primary w-full">
                Sign In
              </button>
            </div>
          </form>
          
          {/* Divider */}
          <div className="divider text-base-content/50 my-6">OR</div>

          {/* Social Login */}
          <div className="form-control">
            <button className="btn btn-outline border-base-content/20 text-base-content">
              <Github className="w-5 h-5 mr-2" />
              Continue with GitHub
            </button>
          </div>

          {/* Sign Up Link */}
          <div className="text-center mt-6">
            <p className="text-sm text-base-content/70">
              Don't have an account?{' '}
              <Link to="/signup" className="link link-primary font-medium">
                Sign Up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}