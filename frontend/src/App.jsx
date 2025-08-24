import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./components/Home";
import About from "./components/About";
import Docs from "./components/Docs";
import LandingPage from "./components/LandingPage";

function App() {
  return (
    <Router>
      <div className="relative min-h-screen text-gray-900">

        <Navbar />

        {/* Routes */}
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/about" element={<About />} />
          <Route path="/docs" element={<Docs />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
