import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { useState, useRef, useEffect } from "react";
import Navbar from "./components/Navbar";
import About from "./components/About";
import Docs from "./components/Docs";
import LandingPage from "./components/LandingPage";
import DocsSidebar from "./components/DocsSidebar";
import { Login, Register } from "./components/AuthComponents";
import ProfileSetup from "./components/ProfileSetup";
import ProtectedProfileRoute from "./components/ProtectedProfileRoute";

function App() {
  const [isDocsOpen, setIsDocsOpen] = useState(false);
  const sidebarRef = useRef(null);

  const toggleDocs = () => {
    setIsDocsOpen(!isDocsOpen);
  };

  const closeDocs = () => {
    setIsDocsOpen(false);
  };

  // Close sidebar when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isDocsOpen && sidebarRef.current && !sidebarRef.current.contains(event.target)) {
        closeDocs();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDocsOpen]);

  return (
    <Router>
      <div className="min-h-screen bg-base-100">
        <Navbar toggleDocs={toggleDocs} />
        
        {/* Documentation Sidebar with ref */}
        <div ref={sidebarRef}>
          <DocsSidebar isOpen={isDocsOpen} onClose={closeDocs} />
        </div>
        
        {/* Overlay when sidebar is open on mobile */}
        {isDocsOpen && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
            onClick={closeDocs}
          />
        )}

        {/* Main Content */}
        <div className={isDocsOpen ? "md:ml-64 transition-all duration-300" : ""}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/about" element={<About />} />
            <Route path="/docs" element={<Docs />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route 
              path="/profile-setup" 
              element={
                <ProtectedProfileRoute requireProfileSetup>
                  <ProfileSetup />
                </ProtectedProfileRoute>
              } 
            />
            {/* Redirect authenticated users to profile setup */}
            <Route 
              path="/dashboard" 
              element={
                <ProtectedProfileRoute>
                  {/* Your dashboard component here */}
                  <div className="min-h-screen flex items-center justify-center">
                    <h1 className="text-4xl font-bold">Dashboard</h1>
                  </div>
                </ProtectedProfileRoute>
              } 
            />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;