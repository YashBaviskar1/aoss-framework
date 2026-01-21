import { Routes, Route } from "react-router-dom";
import { useState, useRef, useEffect } from "react";
import {
  SignedIn,
  SignedOut,
  RedirectToSignIn,
} from "@clerk/clerk-react";

import Navbar from "./components/Navbar";
import About from "./components/About";
import Docs from "./components/Docs";
import LandingPage from "./components/LandingPage";
import DocsSidebar from "./components/DocsSidebar";
import { Login, Register } from "./components/AuthComponents";
import ProfileSetup from "./components/ProfileSetup";
import Dashboard from "./components/Dashboard";
import Compliance from "../frontend/src/components/Compliance";

/* NEW imports */
import GdprConfigure from "../frontend/src/components/GdprConfigure";
import ComplianceCustomize from "./components/ComplianceCustomize";
import OrgPolicy from "../frontend/src/components/OrgPolicy";
import SreSafety from "../frontend/src/components/SreSafety";

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
        </Routes>
      </div>
    </div>
  );
}
