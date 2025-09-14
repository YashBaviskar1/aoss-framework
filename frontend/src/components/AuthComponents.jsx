import { SignIn, SignUp, useAuth } from "@clerk/clerk-react";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

// Redirect component after successful authentication
const RedirectAfterAuth = () => {
  const { isSignedIn } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isSignedIn) {
      // Redirect to homepage after successful login
      navigate("/");
    }
  }, [isSignedIn, navigate]);

  return
};

export const Login = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-base-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-primary/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <img
              src="https://www.secuinfra.com/wp-content/uploads/SOAR_Kreise-1.png"
              alt="Logo"
              className="w-12 h-12"
            />
          </div>
          <h2 className="text-3xl font-bold text-base-content">Welcome back</h2>
          <p className="mt-2 text-base-content/70">Sign in to your AOSS account</p>
        </div>
        <div className="bg-base-100 rounded-2xl shadow-lg border border-base-300 p-6">
          <SignIn 
            routing="path"
            path="/login"
            appearance={{
              elements: {
                rootBox: "w-full",
                card: "shadow-none bg-transparent w-full",
                headerTitle: "text-xl font-bold text-base-content",
                headerSubtitle: "text-base-content/70",
                socialButtonsBlockButton: "border-base-300 hover:bg-base-200",
                socialButtonsBlockButtonText: "text-base-content",
                formButtonPrimary: "bg-primary hover:bg-primary/90",
                footerActionText: "text-base-content/70",
                footerActionLink: "text-primary hover:text-primary/80",
                formFieldInput: "border-base-300 focus:border-primary focus:ring-primary",
                identityPreviewText: "text-base-content",
                formFieldLabel: "text-base-content",
                dividerLine: "bg-base-300",
                dividerText: "text-base-content/70 bg-base-100"
              }
            }}
            afterSignInUrl="/"
            afterSignUpUrl="/"
          />
        </div>
      </div>
      <RedirectAfterAuth />
    </div>
  );
};

export const Register = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-base-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-primary/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <img
              src="https://www.secuinfra.com/wp-content/uploads/SOAR_Kreise-1.png"
              alt="Logo"
              className="w-12 h-12"
            />
          </div>
          <h2 className="text-3xl font-bold text-base-content">Create account</h2>
          <p className="mt-2 text-base-content/70">Get started with AOSS</p>
        </div>
        <div className="bg-base-100 rounded-2xl shadow-lg border border-base-300 p-6">
          <SignUp 
            routing="path"
            path="/register"
            appearance={{
              elements: {
                rootBox: "w-full",
                card: "shadow-none bg-transparent w-full",
                headerTitle: "text-xl font-bold text-base-content",
                headerSubtitle: "text-base-content/70",
                socialButtonsBlockButton: "border-base-300 hover:bg-base-200",
                socialButtonsBlockButtonText: "text-base-content",
                formButtonPrimary: "bg-primary hover:bg-primary/90",
                footerActionText: "text-base-content/70",
                footerActionLink: "text-primary hover:text-primary/80",
                formFieldInput: "border-base-300 focus:border-primary focus:ring-primary",
                identityPreviewText: "text-base-content",
                formFieldLabel: "text-base-content",
                dividerLine: "bg-base-300",
                dividerText: "text-base-content/70 bg-base-100"
              }
            }}
            afterSignInUrl="/"
            afterSignUpUrl="/"
          />
        </div>
      </div>
      <RedirectAfterAuth />
    </div>
  );
};