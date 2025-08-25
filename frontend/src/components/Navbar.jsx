import { Link } from "react-router-dom";
import { useState, useEffect } from "react";
import { Menu, X } from "lucide-react";

function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav className={`fixed top-0 w-full z-50 transition-all duration-300 ${
      isScrolled 
        ? "bg-base-300 backdrop-blur-md shadow-sm border-b border-base-300/30" 
        : "bg-transparent backdrop-blur-md"
    }`}>
      <div className="max-w-7xl mx-auto flex items-center justify-between px-6 py-4">
        {/* Logo */}
        <div className="flex items-center space-x-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-300 ${
            isScrolled ? "bg-primary/20" : "bg-white/20 backdrop-blur-sm"
          }`}>
            <img
              src="https://www.secuinfra.com/wp-content/uploads/SOAR_Kreise-1.png"
              alt="Logo"
              className="w-8 h-8"
            />
          </div>
          <span className={`text-2xl font-bold transition-colors duration-300 ${
            isScrolled ? "text-base-content" : "text-white"
          }`}>
            AOSS
          </span>
        </div>

        {/* Desktop Navigation */}
        <ul className="hidden md:flex space-x-8 font-medium">
          <li>
            <Link 
              to="/" 
              className={`transition-colors duration-200 hover:text-primary px-3 py-2 rounded-lg ${
                isScrolled 
                  ? "text-base-content/80 hover:bg-base-200/50" 
                  : "text-white/90 hover:bg-white/10"
              }`}
            >
              Home
            </Link>
          </li>
          <li>
            <Link 
              to="/about" 
              className={`transition-colors duration-200 hover:text-primary px-3 py-2 rounded-lg ${
                isScrolled 
                  ? "text-base-content/80 hover:bg-base-200/50" 
                  : "text-white/90 hover:bg-white/10"
              }`}
            >
              About
            </Link>
          </li>
          <li>
            <Link 
              to="/docs" 
              className={`transition-colors duration-200 hover:text-primary px-3 py-2 rounded-lg ${
                isScrolled 
                  ? "text-base-content/80 hover:bg-base-200/50" 
                  : "text-white/90 hover:bg-white/10"
              }`}
            >
              Docs
            </Link>
          </li>
          <li>
            <Link 
              to="/pricing" 
              className={`transition-colors duration-200 hover:text-primary px-3 py-2 rounded-lg ${
                isScrolled 
                  ? "text-base-content/80 hover:bg-base-200/50" 
                  : "text-white/90 hover:bg-white/10"
              }`}
            >
              Pricing
            </Link>
          </li>
          <li>
            <Link 
              to="/login" 
              className={`btn btn-sm rounded-full px-6 transition-all duration-300 ${
                isScrolled 
                  ? "btn-primary" 
                  : "bg-white/20 text-white backdrop-blur-sm border-white/20 hover:bg-white/30"
              }`}
            >
              Login
            </Link>
          </li>
        </ul>

        {/* Mobile Menu Button */}
        <button 
          className="md:hidden"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
        >
          {isMenuOpen ? (
            <X className={`w-6 h-6 ${isScrolled ? "text-base-content" : "text-white"}`} />
          ) : (
            <Menu className={`w-6 h-6 ${isScrolled ? "text-base-content" : "text-white"}`} />
          )}
        </button>
      </div>

      {/* Mobile Navigation */}
      {isMenuOpen && (
        <div className="md:hidden bg-white/95 backdrop-blur-lg border-t border-base-300/30">
          <div className="px-6 py-4 space-y-4">
            <Link 
              to="/" 
              className="block py-2 text-base-content hover:text-primary transition-colors"
              onClick={() => setIsMenuOpen(false)}
            >
              Home
            </Link>
            <Link 
              to="/about" 
              className="block py-2 text-base-content hover:text-primary transition-colors"
              onClick={() => setIsMenuOpen(false)}
            >
              About
            </Link>
            <Link 
              to="/docs" 
              className="block py-2 text-base-content hover:text-primary transition-colors"
              onClick={() => setIsMenuOpen(false)}
            >
              Docs
            </Link>
            <Link 
              to="/pricing" 
              className="block py-2 text-base-content hover:text-primary transition-colors"
              onClick={() => setIsMenuOpen(false)}
            >
              Pricing
            </Link>
            <Link 
              to="/login" 
              className="btn btn-primary btn-sm rounded-full px-6 mt-4"
              onClick={() => setIsMenuOpen(false)}
            >
              Login
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}

export default Navbar;