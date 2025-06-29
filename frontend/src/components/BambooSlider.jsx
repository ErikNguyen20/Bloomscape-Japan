import React, { useState, useRef, useEffect } from "react";
import "./BambooSlider.css";
import blossomIcon from "../assets/blossom.svg";

const BambooSlider = ({ min, max, value, onChange, value_display }) => {
  const [rotation, setRotation] = useState(0);
  const prevValue = useRef(value);

  useEffect(() => {
    const delta = value - prevValue.current;
    const direction = delta >= 0 ? 1 : -1;
    setRotation((prev) => prev + direction * Math.abs(delta) * 6);
    prevValue.current = value;
  }, [value]);

  return (
    <div className="bamboo-slider-container">
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={onChange}
        className="bamboo-slider"
        style={{
          "--blossom-icon": `url("${blossomIcon}")`,
          "--rotation": `${rotation}deg`,
        }}
      />
      <div className="bamboo-slider-values">
        <span className="bamboo-slider-min">{min}</span>
        <span className="bamboo-slider-current" title="* = Some cities are predictions for this year">{value_display}</span>
        <span className="bamboo-slider-max">{max}</span>
      </div>
    </div>
  );
};

export default BambooSlider;
