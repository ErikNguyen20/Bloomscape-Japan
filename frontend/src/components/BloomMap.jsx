import { useState, useEffect, useRef } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
  CircleMarker,
  Tooltip
} from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

import eyeIcon from '../assets/eye.svg'
import eyeOffIcon from '../assets/eye-off.svg'

import {
  colormaps,
  getHeatmapColor,
  getDateFromDayOfYear,
  formatDateString
} from '../utils/heatmapUtils';
import ColorBar from "./ColorBar";
import BambooSlider from "./BambooSlider";
import api from '../api';
import LineGraph from "./LineGraph"


const baseLayers = {
    OpenStreetMap: {
      url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    },
    GSI_en: {
      url: "https://cyberjapandata.gsi.go.jp/xyz/english/{z}/{x}/{y}.png",
      attribution: "Map data © Geospatial Information Authority of Japan"
    },
    GSI_jp: {
      url: "https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png",
      attribution: "Map data © Geospatial Information Authority of Japan"
    },
    stadia: {
      url: "https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}.png",
      attribution: '&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://www.stamen.com/" target="_blank">Stamen Design</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    },
    stadia_bg: {
      url: "https://tiles.stadiamaps.com/tiles/stamen_terrain_background/{z}/{x}/{y}{r}.png",
      attribution: '&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://www.stamen.com/" target="_blank">Stamen Design</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }
  };


function MouseCoordinates({ setMouseLatLng }) {
  const map = useMap();

  useEffect(() => {
    const handleMouseMove = (e) => {
      setMouseLatLng({
        lat: e.latlng.lat.toFixed(7),
        lng: e.latlng.lng.toFixed(7),
      });
    };

    map.on('mousemove', handleMouseMove);
    return () => {
      map.off('mousemove', handleMouseMove);
    };
  }, [map, setMouseLatLng]);

  return null;
}


function BloomMap({ SELECTED_MAP_LAYER = "GSI_en", DEFAULT_MIN_DAY_OF_YEAR = 1, DEFAULT_MAX_DAY_OF_YEAR = 160, language="en"}) {
  const CURRENT_YEAR = new Date().getMonth() < 5 ? new Date().getFullYear() : new Date().getFullYear() + 1;

  const [year, setYear] = useState(CURRENT_YEAR);
  const [points, setPoints] = useState([]);
  const [minDayOfYear, setMinDayOfYear] = useState(DEFAULT_MIN_DAY_OF_YEAR);
  const [maxDayOfYear, setMaxDayOfYear] = useState(DEFAULT_MAX_DAY_OF_YEAR);
  const [showPoints, setShowPoints] = useState(true);
  const [containsPredictions, setContainsPredictions] = useState(true);
  const [mouseLatLng, setMouseLatLng] = useState(null);

  const [selectedPoint, setSelectedPoint] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [predictions, setPredictions] = useState(null);


  useEffect(() => {
    const fetchHeatmapData = async () => {
      console.log(`Fetching data for year ${year}...`);

      try {
        const response = await api.get(`/heatmap?year=${year}`);
        const fetchedPoints = response.data || [];
        setPoints(fetchedPoints);
        console.log("Fetched Points:", fetchedPoints)

        if (fetchedPoints.length > 0) {
            const values = fetchedPoints.map(p => p.value);
            setMinDayOfYear(Math.min(...values));
            setMaxDayOfYear(Math.max(...values));

            const preds = fetchedPoints.map(p => p.is_prediction);
            setContainsPredictions(preds.some(Boolean));
        }
      } catch (error) {
        console.error("Error fetching heatmap data:", error);
      }
    };

    fetchHeatmapData();
  }, [year]);


  useEffect(() => {
    const fetchGraphData = async () => {
      if (!selectedPoint) {
        setGraphData(null);
        setPredictions(null);
        return;
      }

      try {
        const response = await api.get(`/history?city=${selectedPoint.city}`);
        const {
          points: fetchedGraph,
          prediction_year,
          prediction_q10,
          prediction_q50,
          prediction_q90
        } = response.data;

        setGraphData(fetchedGraph);
        setPredictions({
          yr: prediction_year,
          q10: prediction_q10,
          q50: prediction_q50,
          q90: prediction_q90
        });
      } catch (error) {
        console.error("Error fetching graph data:", error);
        setGraphData(null);
        setGraphDescription('');
      }
    };

    fetchGraphData();
  }, [selectedPoint]);


  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
    }}>
      <BambooSlider
        min={1953}
        max={CURRENT_YEAR}
        value={year}
        onChange={(e) => setYear(Number(e.target.value))}
        value_display={`${year}${containsPredictions ? '*' : ''}`}
      />

      <div style={{
        width: '90vw',
        maxWidth: '700px',
        aspectRatio: '1 / 1', // keeps the map square
        marginTop: '0.5rem',
      }}>
        <MapContainer
          center={[36, 138]}
          zoom={5}
          maxZoom={11}
          minZoom={4}
          style={{ height: '100%', width: '100%' }}
          maxBounds={[[0, 110], [55, 160]]}
          attributionControl={false}
        >
{/*           <MouseCoordinates setMouseLatLng={setMouseLatLng} /> */}

          <div
            style={{
              position: 'absolute',
              top: '10px',
              right: '10px',
              zIndex: 1000,
            }}
          >
            <button
              onClick={() => setShowPoints(prev => !prev)}
              style={{
                background: 'rgba(255, 255, 255, 0.2)',
                padding: '6px',
                cursor: 'pointer',
                backdropFilter: 'blur(3px)',
                WebkitBackdropFilter: 'blur(3px)',
              }}
              title={showPoints ? "Hide points" : "Show points"}
            >
              <img
                src={showPoints ? eyeIcon : eyeOffIcon}
                alt={showPoints ? "Hide points" : "Show points"}
                style={{ width: '18px', height: '18px' }}
              />
            </button>
          </div>

          {mouseLatLng && (
            <div
              style={{
                position: 'absolute',
                bottom: '5px',
                right: '5px',
                background: 'transparent',
                padding: '6px 10px',
                borderRadius: '4px',
                fontSize: '10px',
                zIndex: 1000,
                color: '#000',
                border: 'none',
              }}
            >
              {language == "en" ? "Lat" : "緯"}: {mouseLatLng.lat}, {language == "en" ? "Lon" : "経"}: {mouseLatLng.lng}
            </div>
          )}

          <TileLayer
            url={baseLayers[SELECTED_MAP_LAYER].url}
            attribution={baseLayers[SELECTED_MAP_LAYER].attribution}
          />

          {showPoints && points.map((point, idx) => (
            <CircleMarker
              key={idx}
              center={[point.lat, point.lng]}
              radius={8}
              pathOptions={{
                color: getHeatmapColor(point.value, DEFAULT_MIN_DAY_OF_YEAR, DEFAULT_MAX_DAY_OF_YEAR),
                fillColor: getHeatmapColor(point.value, DEFAULT_MIN_DAY_OF_YEAR, DEFAULT_MAX_DAY_OF_YEAR),
                fillOpacity: 0.7,
              }}
              eventHandlers={{
                click: () => setSelectedPoint(point),
              }}
            >
              <Tooltip>{language == "en" ? point.city : point.city_jp}: {formatDateString(getDateFromDayOfYear(year, point.value), language)}</Tooltip>
            </CircleMarker>
          ))}

          {showPoints && (<ColorBar colormap={colormaps['hot']} year={year} min={DEFAULT_MIN_DAY_OF_YEAR} max={DEFAULT_MAX_DAY_OF_YEAR} language={language} />)}
        </MapContainer>

        {/* Slide-in panel */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            right: 0,
            height: '100%',
            width: '100%',
            maxWidth: '480px',
            backgroundColor: 'white',
            boxShadow: '-2px 0 5px rgba(0,0,0,0.3)',
            transform: selectedPoint ? 'translateX(0)' : 'translateX(100%)',
            transition: 'transform 0.3s ease-in-out',
            zIndex: 2000,
            overflowY: 'auto',
          }}
        >
          {selectedPoint && (
            <div style={{ padding: '1rem' }}>
              <button onClick={() => setSelectedPoint(null)} style={{ float: 'right' }}>
                {language == "en" ? "Close" : "閉じる"}
              </button>
              <br></br>
              {graphData ? (
                <LineGraph
                  data={graphData}
                  title={language == "en" ? `${selectedPoint.city} Historic Bloom Dates` : `${selectedPoint.city_jp} 歴史的な開花日`}
                  xDataKey="year"
                  yDataKey="value"
                  xLabel={language == "en" ? "Year" : "年"}
                  yLabel={language == "en" ? "Day" : "通算日 (Day)"}
                  language={language}
                />
              ) : (
                <p>Loading data...</p>
              )}

              {predictions && (
              <p>
                {language == "en" ? "Estimated bloom date" : "開花予想日"}: <strong>{formatDateString(getDateFromDayOfYear(predictions.yr, Math.round(predictions.q50)), language, true)}</strong>,<br />
                {language == "en" ? "80% prediction interval" : "80%予測区間"}: <strong>{formatDateString(getDateFromDayOfYear(predictions.yr, Math.round(predictions.q10)), language, true)} – {formatDateString(getDateFromDayOfYear(predictions.yr, Math.round(predictions.q90)), language, true)}</strong>
              </p>
            )}

            </div>
          )}
        </div>


      </div>
    </div>
  );
}

export default BloomMap;

