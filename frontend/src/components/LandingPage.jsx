import { useState, useEffect } from 'react';
import { useNavigate } from "react-router-dom";
import { 
  ChevronRight, 
  Zap, 
  Brain, 
  Network, 
  Shield, 
  BarChart3, 
  Terminal, 
  Cpu, 
  Play,
  Sparkles,
  ArrowRight,
  Github,
  Server,
  Database,
  Code,
  BarChart,
  Cloud,
  Settings
} from 'lucide-react';

export default function LandingPage() {
  const [isVisible, setIsVisible] = useState(false);
  const navigate = useNavigate();

  const goToChat = () => {
    navigate("/chat"); // this will go to your chat route
  };
  useEffect(() => {
    setIsVisible(true);
  }, []);

  const features = [
    {
      icon: Brain,
      title: "AI-Powered Intelligence",
      description: "Advanced natural language processing transforms complex requirements into actionable system tasks with intelligent context awareness."
    },
    {
      icon: Network,
      title: "Multi-Agent Architecture",
      description: "Distributed agent system coordinates seamlessly across infrastructure components, ensuring scalable and resilient operations."
    },
    {
      icon: Zap,
      title: "Lightning Fast Execution",
      description: "Optimized RAG implementation delivers sub-second response times for critical system operations and monitoring tasks."
    },
    {
      icon: Shield,
      title: "Enterprise Security",
      description: "Built-in security protocols and audit trails ensure compliance while maintaining the highest standards of system integrity."
    },
    {
      icon: BarChart3,
      title: "Advanced Analytics",
      description: "Real-time insights and predictive analysis help prevent issues before they impact your systems and users."
    },
    {
      icon: Terminal,
      title: "DevOps Integration",
      description: "Seamlessly integrates with existing CI/CD pipelines and infrastructure as code for unified operations management."
    }
  ];

  const stats = [
    { number: "99.9%", label: "Uptime Guarantee" },
    { number: "< 100ms", label: "Response Time" },
    { number: "500+", label: "Automated Tasks" },
    { number: "24/7", label: "Monitoring" }
  ];

  const integrations = [
    { icon: Cloud, name: "Cloud Platforms" },
    { icon: Database, name: "Databases" },
    { icon: Server, name: "Server Infrastructure" },
    { icon: Code, name: "CI/CD Tools" },
    { icon: BarChart, name: "Monitoring Systems" },
    { icon: Settings, name: "Configuration Mgmt" }
  ];

  return (
    <div className="min-h-screen bg-base-100">
      {/* Hero Section */}
      <section className="pt-36 pb-36 px-6 bg-gradient-to-br from-blue-50 via-base-100 to-blue-50">
        <div className="max-w-7xl mx-auto">
          <div className={`text-center transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
            <div className="text-base-content badge badge-outline badge-lg badge-primary mb-6 gap-2 animate-pulse">
              <Sparkles className="w-4 h-4" />
              Now with Advanced RAG Technology
            </div>
            
            <h1 className="text-5xl md:text-6xl font-bold text-base-content mb-6 leading-tight">
              Automated 
              <span className="text-primary block mt-2">
                Orchestration Framework
              </span>
              <span className="text-3xl md:text-4xl text-base-content/70 block mt-4">
                for SRE & System Administration
              </span>
            </h1>
            
            <p className="text-xl text-base-content/70 mb-12 max-w-3xl mx-auto leading-relaxed">
              Transform natural language into powerful system operations. Our AI-powered multi-agent framework 
              revolutionizes infrastructure management with intelligent automation and real-time insights.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <button onClick={goToChat} className="btn btn-primary btn-lg rounded-full hover:shadow-xl transform hover:scale-105 transition-all duration-300 group">
                Start Free Trial
                <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </button>
              <button className="btn btn-outline btn-lg rounded-full border-base-content/20 text-base-content group">
                <Play className="w-5 h-5 mr-2" />
                Watch Demo
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 px-6 bg-base-100">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center group" style={{ transitionDelay: `${index * 100}ms` }}>
                <div className={`text-4xl md:text-5xl font-bold text-primary mb-2 transition-all duration-500 ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
                  {stat.number}
                </div>
                <div className="text-base-content/70 text-sm uppercase tracking-wider">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6 bg-base-100">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-base-content mb-6">
              Powerful Features for Modern 
              <span className="text-primary"> Infrastructure</span>
            </h2>
            <p className="text-xl text-base-content/70 max-w-3xl mx-auto">
              Built for enterprise-scale operations with cutting-edge AI technology
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index}
                className={`card bg-base-100 shadow-lg hover:shadow-xl border border-base-200 transition-all duration-500 transform hover:-translate-y-2 ${isVisible ? 'opacity-100' : 'opacity-0'}`}
                style={{ transitionDelay: `${index * 100}ms` }}
              >
                <div className="card-body items-center text-center">
                  <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mb-6 transition-transform duration-300 group-hover:scale-110">
                    <feature.icon className="w-8 h-8 text-primary" />
                  </div>
                  <h3 className="card-title text-base-content mb-4">
                    {feature.title}
                  </h3>
                  <p className="text-base-content/70">
                    {feature.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Integrations Section */}
      <section className="py-16 px-6 bg-base-200">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-base-content mb-4">
              Seamless Integrations
            </h2>
            <p className="text-lg text-base-content/70 max-w-2xl mx-auto">
              Connect with your existing tools and infrastructure for a unified workflow
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
            {integrations.map((item, index) => (
              <div key={index} className="flex flex-col items-center p-4 bg-base-100 rounded-xl shadow-sm border border-base-300">
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-3">
                  <item.icon className="w-6 h-6 text-primary" />
                </div>
                <span className="text-sm text-base-content/80">{item.name}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Demo Section */}
      <section className="py-24 px-6 bg-base-100">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-base-content mb-6">
              See It In 
              <span className="text-primary"> Action</span>
            </h2>
            <p className="text-xl text-base-content/70">
              Experience the power of natural language system administration
            </p>
          </div>
          
          <div className="card bg-base-100 shadow-xl border border-base-300">
            <div className="card-body">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                </div>
                <div className="text-base-content/70 text-sm">SRE Orchestrator Terminal</div>
              </div>
              
              <div className="font-mono text-sm space-y-4 bg-neutral p-6 rounded-lg text-neutral-content">
                <div className="flex items-center space-x-2">
                  <span className="text-accent">$</span>
                  <span>orchestrate "scale web servers to handle 10x traffic spike"</span>
                </div>
                <div className="text-success ml-4">
                  ✓ Analyzing current infrastructure capacity...<br/>
                  ✓ Calculating optimal scaling parameters...<br/>
                  ✓ Deploying 15 additional web server instances...<br/>
                  ✓ Configuring load balancer rules...<br/>
                  ✓ Traffic spike mitigation complete - Ready for 10x load
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-accent">$</span>
                  <span className="animate-pulse">_</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-16 px-6 bg-base-200">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-base-content mb-4">
              Trusted by Engineering Teams
            </h2>
            <p className="text-lg text-base-content/70 max-w-2xl mx-auto">
              See what developers and SREs are saying about our platform
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="card bg-base-100 shadow-md border border-base-300">
              <div className="card-body">
                <div className="flex items-center mb-4">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <svg key={star} className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="text-base-content/80 mb-4">
                  "This framework has reduced our incident response time by 80%. The natural language interface makes complex operations accessible to our entire team."
                </p>
                <div className="flex items-center">
                  <div className="avatar placeholder mr-3">
                    <div className="bg-neutral text-neutral-content rounded-full w-10">
                      <span>JD</span>
                    </div>
                  </div>
                  <div>
                    <div className="font-medium text-base-content">Jane Doe</div>
                    <div className="text-sm text-base-content/60">Lead SRE, TechCorp</div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="card bg-base-100 shadow-md border border-base-300">
              <div className="card-body">
                <div className="flex items-center mb-4">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <svg key={star} className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="text-base-content/80 mb-4">
                  "The multi-agent architecture is revolutionary. We've automated hundreds of tasks that used to require manual intervention."
                </p>
                <div className="flex items-center">
                  <div className="avatar placeholder mr-3">
                    <div className="bg-neutral text-neutral-content rounded-full w-10">
                      <span>JS</span>
                    </div>
                  </div>
                  <div>
                    <div className="font-medium text-base-content">John Smith</div>
                    <div className="text-sm text-base-content/60">DevOps Engineer, CloudStart</div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="card bg-base-100 shadow-md border border-base-300">
              <div className="card-body">
                <div className="flex items-center mb-4">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <svg key={star} className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="text-base-content/80 mb-4">
                  "The RAG integration with our documentation has been a game-changer. Agents now make decisions based on our actual policies and procedures."
                </p>
                <div className="flex items-center">
                  <div className="avatar placeholder mr-3">
                    <div className="bg-neutral text-neutral-content rounded-full w-10">
                      <span>AR</span>
                    </div>
                  </div>
                  <div>
                    <div className="font-medium text-base-content">Amanda Rodriguez</div>
                    <div className="text-sm text-base-content/60">CTO, DataSecure</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 bg-base-100">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-base-content mb-6">
            Ready to Transform Your 
            <span className="text-primary"> Infrastructure?</span>
          </h2>
          <p className="text-xl text-base-content/70 mb-12">
            Join thousands of SRE teams already using our AI-powered orchestration platform
          </p>
          
          <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
            <button className="btn btn-primary btn-lg rounded-full hover:shadow-xl transform hover:scale-105 transition-all duration-300 group">
              Start Your Free Trial
              <ChevronRight className="w-6 h-6 ml-2 group-hover:translate-x-1 transition-transform" />
            </button>
            <button className="btn btn-outline btn-lg rounded-full border-base-content/20 text-base-content">
              <Github className="w-5 h-5 mr-2" />
              View on GitHub
            </button>
          </div>
          
          <p className="text-sm text-base-content/50 mt-8">
            No credit card required • 14-day free trial • Cancel anytime
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 bg-base-200">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-6 md:mb-0">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Cpu className="w-5 h-5 text-primary-content" />
              </div>
              <span className="text-base-content font-semibold">SRE Orchestrator</span>
            </div>
            
            <div className="flex items-center space-x-8 text-base-content/70 text-sm">
              <a href="#" className="hover:text-base-content transition-colors">Privacy</a>
              <a href="#" className="hover:text-base-content transition-colors">Terms</a>
              <a href="#" className="hover:text-base-content transition-colors">Documentation</a>
              <a href="#" className="hover:text-base-content transition-colors">Support</a>
            </div>
          </div>
          
          <div className="mt-8 pt-8 border-t border-base-content/10 text-center text-base-content/50 text-sm">
            © 2025 SRE Orchestrator. Built for the future of infrastructure management.
          </div>
        </div>
      </footer>
    </div>
  );
}