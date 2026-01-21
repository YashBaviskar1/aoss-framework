import { SignedIn, SignedOut, RedirectToSignIn } from "@clerk/clerk-react";
import { useNavigate } from "react-router-dom";

const ProtectedProfileRoute = ({ children, requireProfileSetup = false }) => {
  const navigate = useNavigate();
  
  // Check if profile is already set up (you would implement this logic)
  const isProfileSetup = localStorage.getItem('profileSetup') === 'true';

  if (requireProfileSetup && !isProfileSetup) {
    // Force profile setup before accessing other pages
    return (
      <SignedIn>
        {children}
      </SignedIn>
    );
  }

  return (
    <>
      <SignedIn>
        {children}
      </SignedIn>
      <SignedOut>
        <RedirectToSignIn />
      </SignedOut>
    </>
  );
};

export default ProtectedProfileRoute;