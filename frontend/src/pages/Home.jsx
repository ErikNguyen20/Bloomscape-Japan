import { useState } from "react";
import { useLanguage } from "../contexts/LanguageContext";
import BloomMap from "../components/BloomMap";
import LineGraph from "../components/LineGraph";
import "./Home.css";

const Home = () => {
  const { language, setLanguage } = useLanguage();

  const handleLanguageChange = (lang) => {
    setLanguage(lang);
  };

  return (
    <div className="home-page">
      <div className="language-selector">
        <button
          onClick={() => handleLanguageChange("jp")}
          style={{
            textDecoration: language === "jp" ? "underline" : "none",
          }}
        >
          日本語
        </button>
        {" / "}
        <button
          onClick={() => handleLanguageChange("en")}
          style={{
            textDecoration: language === "en" ? "underline" : "none",
          }}
        >
          English
        </button>
      </div>

      <header className="header">
        <h1>{language === "en" ? "Bloomscape Japan" : "ブルームスケープ・ジャパン"}</h1>
      </header>

      <div className="map-container">
        <div className="map-content">
          <BloomMap
            SELECTED_MAP_LAYER={language === "en" ? "GSI_en" : "GSI_jp"}
            language={language}
          />
        </div>
      </div>
    </div>
  );
};

export default Home;

