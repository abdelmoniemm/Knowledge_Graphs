// client/src/index.js
import React from "react";
import './styles.css';

import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import App from "./App";              // your existing dashboard page (unchanged)
import GenAIPage from "./GenAIPage";
import ShaclRunner from "./ShaclRunner";

 
  

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<App />} />
      <Route path="/genai" element={<GenAIPage />} />
      <Route path="/shacl" element={<ShaclRunner />} />
    </Routes>
  </BrowserRouter>
);
