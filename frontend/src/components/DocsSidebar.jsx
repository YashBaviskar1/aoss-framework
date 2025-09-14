import { X, BookOpen, ChevronRight } from "lucide-react";

const DocsSidebar = ({ isOpen, onClose }) => {
  const docSections = [
    {
      title: "GET STARTED WITH AOSS",
      items: [
        "Getting Started >",
        "Tutorial >",
        "Architecture >",
        "Installation Guide >",
        "User Interface >"
      ]
    },
    {
      title: "BUILD WITH AOSS",
      items: [
        "Concepts >",
        "Workflow Components >",
        "Multi-Language Script Tasks >",
        "AI Tools >",
        "Version Control & CI/CD >",
        "Plugin Developer Guide >"
      ]
    },
    {
      title: "HOW-TO GUIDES",
      items: []
    },
    {
      title: "SCALE WITH AOSS",
      items: [
        "Cloud & Enterprise Edition >",
        "Task Runners >"
      ]
    },
    {
      title: "BEST PRACTICES",
      items: []
    },
    {
      title: "MANAGE AOSS",
      items: [
        "Administrator Guide >",
        "Migration Guide >",
        "Performance >"
      ]
    },
    {
      title: "REFERENCE DOCS",
      items: [
        "Configuration >",
        "Expressions >",
        "API Reference >",
        "Terraform Provider >",
        "Server CLI >",
        "AOSS EE CLI >"
      ]
    }
  ];

  return (
    <>
      {/* Mobile Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-base-100 shadow-xl transform transition-transform duration-300 ease-in-out
        md:hidden ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex items-center justify-between p-4 border-b border-base-300">
          <div className="flex items-center space-x-2">
            <BookOpen className="w-5 h-5 text-primary" />
            <span className="font-semibold text-base-content">Documentation</span>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-base-200 transition-colors">
            <X className="w-5 h-5 text-base-content" />
          </button>
        </div>
        
        <div className="h-full overflow-y-auto p-4">
          {docSections.map((section, index) => (
            <div key={index} className="mb-6">
              <h3 className="text-xs font-semibold text-base-content/60 uppercase tracking-wider mb-3">
                {section.title}
              </h3>
              <ul className="space-y-2">
                {section.items.map((item, itemIndex) => (
                  <li key={itemIndex}>
                    <button 
                      className="flex items-center justify-between w-full text-sm text-base-content p-2 rounded-lg hover:bg-primary/10 hover:text-primary transition-all duration-200 group"
                    >
                      <span className="text-left">{item}</span>
                      <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity duration-200 text-primary" />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Desktop Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-40 w-64 bg-base-100 border-r border-base-300 shadow-sm transform transition-transform duration-300 ease-in-out
        hidden md:block ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex items-center justify-between p-4 border-b border-base-300">
          <div className="flex items-center space-x-2">
            <BookOpen className="w-5 h-5 text-primary" />
            <span className="font-semibold text-base-content">Documentation</span>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-base-200 transition-colors">
            <X className="w-5 h-5 text-base-content" />
          </button>
        </div>
        
        <div className="h-full overflow-y-auto p-4">
          {docSections.map((section, index) => (
            <div key={index} className="mb-6">
              <h3 className="text-xs font-semibold text-base-content/60 uppercase tracking-wider mb-3">
                {section.title}
              </h3>
              <ul className="space-y-2">
                {section.items.map((item, itemIndex) => (
                  <li key={itemIndex}>
                    <button 
                      className="flex items-center justify-between w-full text-sm text-base-content p-2 rounded-lg hover:bg-primary/10 hover:text-primary transition-all duration-200 group"
                    >
                      <span className="text-left">{item}</span>
                      <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity duration-200 text-primary" />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </>
  );
};

export default DocsSidebar;