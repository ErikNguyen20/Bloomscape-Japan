import React from "react";
import { Routes, Route } from "react-router-dom";
import { LanguageProvider } from "./contexts/LanguageContext";

import Home from "./pages/Home";
import './App.css'


const App = () => {
  return (
    <LanguageProvider>
      <Routes>
        <Route path="/" element={<Home />} />
        {/* <Route path="/about" element={<About />} /> */}
        {/* <Route path="/contact" element={<Contact />} /> */}
      </Routes>
    </LanguageProvider>
  );
};

export default App;
