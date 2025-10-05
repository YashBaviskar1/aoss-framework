import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./components/Home";
import About from "./components/About";
import Docs from "./components/Docs";
import LandingPage from "./components/LandingPage";
import Chat from "./components/Chat";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";
import Compliance from "./components/Compliance";

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
          <Route path = "/chat" element = {<Chat/>}/>
          <Route path = "/login" element = {<Login/>}/>
          <Route path = "/dashboard" element = {<Dashboard/>} />
          <Route path="/compliance" element={<Compliance />} />

        </Routes>
      </div>
    </Router>
  );
}

export default App;
