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

export default function App() {
  const [isDocsOpen, setIsDocsOpen] = useState(false);
  const sidebarRef = useRef(null);

  const toggleDocs = () => setIsDocsOpen(!isDocsOpen);
  const closeDocs = () => setIsDocsOpen(false);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isDocsOpen && sidebarRef.current && !sidebarRef.current.contains(event.target)) {
        closeDocs();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isDocsOpen]);

  return (
    <div className="min-h-screen bg-base-100">
      <Navbar toggleDocs={toggleDocs} />

      <div ref={sidebarRef}>
        <DocsSidebar isOpen={isDocsOpen} onClose={closeDocs} />
      </div>

      {isDocsOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={closeDocs}
        />
      )}

      <div className={isDocsOpen ? "md:ml-64 transition-all duration-300" : ""}>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/about" element={<About />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="/login/*" element={<Login />} />
          <Route path="/register/*" element={<Register />} />

          {/* Protected routes */}
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
        </Routes>
      </div>
    </div>
  );
}


