function About() {
  return (
    <div className="px-6 py-16 text-center">
      <h2 className="text-4xl text-primary font-bold mb-4">About AOSS</h2>
      <p className="text-lg text-white max-w-3xl mx-auto">
        The proposed project, Automated Orchestration Framework for SRE and System 
Administration (AOSS), aims to develop an AI-powered assistant capable of executing 
complex Site Reliability Engineering (SRE) and system administration tasks from natural 
language instructions. By integrating a multi-agent architecture comprising specialized agents 
for planning, execution, error handling, and networking with retrieval-augmented generation 
(RAG) over organizational documentation, the system ensures compliance with operational 
policies while maintaining adaptability. The framework will feature real-time observability 
through Grafana dashboards, automated daily reporting for auditability, and self-healing 
capabilities to reduce human intervention. Targeted domains include networking, databases, 
deployments, firewalls, and file systems, with agents collaborating via message queues and 
employing context-aware reasoning to resolve operational issues autonomously. This solution 
seeks to minimize manual toil, improve operational efficiency, and provide organizations 
with an intelligent, secure, and transparent orchestration platform for critical infrastructure 
management.
      </p>
    </div>
  );
}

export default About;
