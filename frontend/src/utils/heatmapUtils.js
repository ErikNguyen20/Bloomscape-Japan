// Color maps
export const colormaps = {
  jet: [
    [0, 0, 255],    // Blue
    [0, 255, 255],  // Cyan
    [0, 255, 0],    // Green
    [255, 255, 0],  // Yellow
    [255, 0, 0],    // Red
  ],
  hot: [
    [0, 0, 0],      // Black
    [255, 0, 0],    // Red
    [255, 255, 0],  // Yellow
    [255, 255, 255] // White
  ],
  coolwarm: [
    [59, 76, 192],   // Cool Blue
    [221, 221, 221], // Neutral
    [180, 4, 38]     // Warm Red
  ]
};

// Interpolate color from colormap
export function getHeatmapColor(value, min, max, colormap = colormaps.hot) {
  if (max === min) return `rgb(${colormap[colormap.length - 1].join(",")})`;

  const ratio = (value - min) / (max - min);
  const numSegments = colormap.length - 1;
  const segment = Math.min(Math.floor(ratio * numSegments), numSegments - 1);
  const localRatio = (ratio * numSegments) - segment;

  const [r1, g1, b1] = colormap[segment];
  const [r2, g2, b2] = colormap[segment + 1];

  const r = Math.round(r1 + localRatio * (r2 - r1));
  const g = Math.round(g1 + localRatio * (g2 - g1));
  const b = Math.round(b1 + localRatio * (b2 - b1));

  return `rgb(${r}, ${g}, ${b})`;
}

// Convert year and day-of-year to a Date
export function getDateFromDayOfYear(year, dayOfYear) {
  const date = new Date(year, 0);
  date.setDate(dayOfYear);
  return date;
}

// Format Date as "Jan 21"
export function formatDateString(date, language = "en", includeYear = false) {
  const options = {
    month: 'short',
    day: 'numeric',
    ...(includeYear && { year: 'numeric' })
  };
  const locale = language === "en" ? "en-US" : "ja-JP";
  return date.toLocaleDateString(locale, options);
}
