import React from "react";
import { getDateFromDayOfYear, formatDateString } from '../utils/heatmapUtils';


function colormapToCSSGradient(colormap) {
  const n = colormap.length;
  const stops = colormap.map((color, i) => {
    const [r, g, b] = color;
    const pct = (i / (n - 1)) * 100;
    return `rgb(${r}, ${g}, ${b}) ${pct}%`;
  });
  return `linear-gradient(to right, ${stops.join(", ")})`;
}

const ColorBar = ({ colormap, year, min = 1, max = 200, language = "en"}) => {
  const gradient = colormapToCSSGradient(colormap);

  return (
    <div
      style={{
        position: "absolute",
        bottom: "20px",
        left: "20px",
        backgroundColor: "white",
        padding: "8px 12px",
        borderRadius: "8px",
        boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
        fontSize: "12px",
        zIndex: 1000
      }}
    >
      <div
        style={{
          width: "200px",
          height: "15px",
          background: gradient,
          marginBottom: "6px",
          border: "1px solid #aaa"
        }}
      />
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <span>{formatDateString(getDateFromDayOfYear(year, min), language)}</span>
        <span>{formatDateString(getDateFromDayOfYear(year, (min + max) / 2), language)}</span>
        <span>{formatDateString(getDateFromDayOfYear(year, max), language)}</span>
      </div>
    </div>
  );
};

export default ColorBar;
