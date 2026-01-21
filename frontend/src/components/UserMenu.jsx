import { useUser, useClerk } from "@clerk/clerk-react";
import { LogOut, User, Settings } from "lucide-react";
import { useState, useRef, useEffect } from "react";

const UserMenu = () => {
  const { user } = useUser();
  const { signOut } = useClerk();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const handleSignOut = async () => {
    try {
      await signOut();
      // Redirect to homepage after successful sign out
      window.location.href = window.location.origin;
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-2 rounded-lg hover:bg-base-200 transition-colors duration-200"
      >
        <img
          src={user?.imageUrl}
          alt="Profile"
          className="w-8 h-8 rounded-full"
        />
        <span className="text-base-content hidden md:block">
          {user?.firstName}
        </span>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-base-100 rounded-lg shadow-lg border border-base-300 py-1 z-50">
          <div className="px-4 py-2 border-b border-base-300">
            <p className="text-sm font-medium text-base-content">{user?.fullName}</p>
            <p className="text-xs text-base-content/70">{user?.primaryEmailAddress?.emailAddress}</p>
          </div>
          
          <button className="w-full text-left px-4 py-2 text-sm text-base-content hover:bg-base-200 flex items-center gap-2">
            <User className="w-4 h-4" />
            Profile
          </button>
          
          <button className="w-full text-left px-4 py-2 text-sm text-base-content hover:bg-base-200 flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Settings
          </button>
          
          <div className="border-t border-base-300 my-1"></div>
          
          <button
            onClick={handleSignOut}
            className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-base-200 flex items-center gap-2"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      )}
    </div>
  );
};

export default UserMenu;