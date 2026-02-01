import { Routes, Route, useNavigate } from "react-router-dom";
import { useState, useRef, useEffect } from "react";
import {
  SignedIn,
  SignedOut,
  RedirectToSignIn,
  useUser,
} from "@clerk/clerk-react";

import Navbar from "./components/Navbar";
import About from "./components/About";
import Docs from "./components/Docs";
import LandingPage from "./components/LandingPage";
import DocsSidebar from "./components/DocsSidebar";
import { Login, Register } from "./components/AuthComponents";
import ProfileSetup from "./components/ProfileSetup";
import Dashboard from "./components/Dashboard";
import Compliance from "./components/Compliance";

/* NEW imports */
import GdprConfigure from "./components/GdprConfigure";
import ComplianceCustomize from "./components/ComplianceCustomize";
import OrgPolicy from "./components/OrgPolicy";
import SreSafety from "./components/SreSafety";
import ChatOrchestrator from "./components/ChatOrchestrator";

// Separate component for Auth Logic to use hooks inside Routes
const AuthRouteHandler = ({ component: Component }) => {
  const { user, isLoaded } = useUser();
  const navigate = useNavigate();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    if (isLoaded && user) {
      // Check if user exists in our DB
      fetch(`http://localhost:8000/api/user/${user.id}/status`)
        .then(res => res.json())
        .then(data => {
          if (data.exists) {
            // If trying to access profile-setup but already exists, maybe redirect to dashboard?
            // But here we are just wrapping component. 
            // Let's rely on specific route logic or just Render.
            // Actually, the requirement: "if existing user -> direct to /dashboard"
            // We can handle this by checking current path or forcing dashboard availability.
            setIsChecking(false);
          } else {
            // New user
            // If specific route logic is needed we can add it here.
            setIsChecking(false);
          }
        })
        .catch(err => {
          console.error("API Error", err);
          setIsChecking(false);
        });
    } else if (isLoaded && !user) {
      setIsChecking(false);
    }
  }, [isLoaded, user]);

  if (!isLoaded || isChecking) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return <Component />;
};

// Wrapper specifically for the "Smart" routing
const SmartRedirect = () => {
  const { user, isLoaded } = useUser();
  const navigate = useNavigate();

  useEffect(() => {
    if (isLoaded && user) {
      fetch(`http://localhost:8000/api/user/${user.id}/status`)
        .then(res => res.json())
        .then(data => {
          if (data.exists) {
            navigate('/dashboard');
          } else {
            navigate('/profile-setup');
          }
        })
        .catch(err => console.error("API error", err));
    }
  }, [isLoaded, user, navigate]);

  return <div className="min-h-screen flex items-center justify-center">Checking account status...</div>;
}

export default function App() {
  const [isDocsOpen, setIsDocsOpen] = useState(false);
  const sidebarRef = useRef(null);

  const toggleDocs = () => setIsDocsOpen(!isDocsOpen);
  const closeDocs = () => setIsDocsOpen(false);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        isDocsOpen &&
        sidebarRef.current &&
        !sidebarRef.current.contains(event.target)
      ) {
        closeDocs();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () =>
      document.removeEventListener("mousedown", handleClickOutside);
  }, [isDocsOpen]);

  return (
    <div className="min-h-screen bg-base-100">
      {/* Navbar */}
      <div className="relative z-50">
        <Navbar toggleDocs={toggleDocs} />
      </div>

      {/* Docs Sidebar */}
      <div ref={sidebarRef}>
        <DocsSidebar isOpen={isDocsOpen} onClose={closeDocs} />
      </div>

      {/* Mobile overlay */}
      {isDocsOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={closeDocs}
        />
      )}

      {/* Main content */}
      <div className={isDocsOpen ? "md:ml-64 transition-all duration-300" : ""}>
        <Routes>
          {/* Public */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/about" element={<About />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="/login/*" element={<Login />} />
          <Route path="/register/*" element={<Register />} />

          {/* Smart Redirect for logged in users landing explicitly or needing check */}
          <Route path="/auth-check" element={
            <>
              <SignedIn>
                <SmartRedirect />
              </SignedIn>
              <SignedOut>
                <RedirectToSignIn />
              </SignedOut>
            </>
          } />

          {/* Profile setup */}
          <Route
            path="/profile-setup"
            element={
              <>
                <SignedIn>
                  <ProfileSetup />
                </SignedIn>
                <SignedOut>
                  <RedirectToSignIn />
                </SignedOut>
              </>
            }
          />

          {/* Dashboard */}
          <Route
            path="/dashboard"
            element={
              <>
                <SignedIn>
                  <Dashboard />
                </SignedIn>
                <SignedOut>
                  <RedirectToSignIn />
                </SignedOut>
              </>
            }
          />

          {/* Compliance landing */}
          <Route
            path="/compliance"
            element={
              <>
                <SignedIn>
                  <Compliance />
                </SignedIn>
                <SignedOut>
                  <RedirectToSignIn />
                </SignedOut>
              </>
            }
          />

          {/* GDPR configure (graph-backed) */}
          <Route
            path="/compliance/gdpr"
            element={
              <>
                <SignedIn>
                  <GdprConfigure />
                </SignedIn>
                <SignedOut>
                  <RedirectToSignIn />
                </SignedOut>
              </>
            }
          />

          {/* Organizational Policy */}
          <Route
            path="/compliance/org-policy"
            element={
              <>
                <SignedIn>
                  <OrgPolicy />
                </SignedIn>
                <SignedOut>
                  <RedirectToSignIn />
                </SignedOut>
              </>
            }
          />

          {/* Platform / SRE Safety */}
          <Route
            path="/compliance/sre-safety"
            element={
              <>
                <SignedIn>
                  <SreSafety />
                </SignedIn>
                <SignedOut>
                  <RedirectToSignIn />
                </SignedOut>
              </>
            }
          />

          {/* YAML / rules customize (OLD UI) */}
          <Route
            path="/compliance/customize"
            element={
              <>
                <SignedIn>
                  <ComplianceCustomize />
                </SignedIn>
                <SignedOut>
                  <RedirectToSignIn />
                </SignedOut>
              </>
            }
          />

          {/* Orchestrator Chat */}
          <Route
            path="/chat"
            element={
              <>
                <SignedIn>
                  <ChatOrchestrator />
                </SignedIn>
                <SignedOut>
                  <RedirectToSignIn />
                </SignedOut>
              </>
            }
          />
        </Routes>
      </div>
    </div >
  );
}
