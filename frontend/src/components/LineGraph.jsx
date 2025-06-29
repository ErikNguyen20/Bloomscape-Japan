import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { getDateFromDayOfYear, formatDateString } from '../utils/heatmapUtils';


const getLinearRegressionAndR = (data, xKey, yKey) => {
  const n = data.length;

  let sumX = 0;
  let sumY = 0;
  let sumXX = 0;
  let sumYY = 0;
  let sumXY = 0;

  for (const d of data) {
    const x = d[xKey];
    const y = d[yKey];

    sumX += x;
    sumY += y;
    sumXX += x * x;
    sumYY += y * y;
    sumXY += x * y;
  }

  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;

  const numerator = n * sumXY - sumX * sumY;
  const denominator = Math.sqrt(
    (n * sumXX - sumX * sumX) * (n * sumYY - sumY * sumY)
  );

  const r = numerator / denominator;

  return { slope, intercept, r };
};


const fillMissingYears = (data, xKey, yKey) => {
  const years = data.map(d => d[xKey]);
  const minYear = Math.min(...years);
  const maxYear = Math.max(...years);

  const yearMap = Object.fromEntries(data.map(d => [d[xKey], d[yKey]]));

  const filled = [];
  for (let year = minYear; year <= maxYear; year++) {
    filled.push({
      [xKey]: year,
      [yKey]: yearMap[year] !== undefined ? yearMap[year] : null,
    });
  }
  return filled;
};


const LineGraph = ({ data, title, xDataKey, yDataKey, xLabel, yLabel, language="en"}) => {
  const completeData = fillMissingYears(data, xDataKey, yDataKey);

  const validData = completeData.filter(d => d[yDataKey] != null);
  const { slope, intercept, r } = getLinearRegressionAndR(validData, xDataKey, yDataKey);

  const dataWithTrend = completeData.map(d => ({
    ...d,
    trendValue: (slope * d[xDataKey] + intercept).toFixed(3),
  }));

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-1">{title}</h2>
      <p className="text-gray-600 text-sm mb-4">{language == "en" ? "Correlation (r)" : "相関 (r)"}: {r.toFixed(3)}</p>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={dataWithTrend}
          margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey={xDataKey}
            label={{ value: xLabel, position: 'insideBottom', offset: -10 }}
          />
          <YAxis
            domain={[
              (dataMin) => Math.floor(dataMin * 0.9),
              (dataMax) => Math.ceil(dataMax * 1.1)
            ]}
            tickFormatter={(dayOfYear) => {
              const date = getDateFromDayOfYear(2025, dayOfYear);
              return formatDateString(date, language);
            }}

          />

            <Tooltip
              formatter={(value, name, props) => {
                const year = props.payload[xDataKey];
                if (name === yDataKey || name === yLabel) {
                  if (year == null || value == null) return [value, yLabel];

                  const date = getDateFromDayOfYear(year, value);
                  return [formatDateString(date, language), yLabel]; // <-- force name here
                }
                if (name === 'trendValue' || name === 'Trendline' || name === "トレンドライン") {
                  const date = getDateFromDayOfYear(year, Math.round(value));
                  return [formatDateString(date, language), language === "en" ? 'Trendline' : "トレンドライン"];
                }
                return [value, name];
              }}
            />

          <Legend verticalAlign="top" align="right" />
         <Line
            type="monotone"
            dataKey={yDataKey}
            name={yLabel}
            stroke="#8884d8"
            dot={true}
            connectNulls={true}
          />

          <Line
            type="linear"
            dataKey="trendValue"
            name={language == "en" ? 'Trendline' : "トレンドライン"}
            stroke="#FF0000"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default LineGraph;
