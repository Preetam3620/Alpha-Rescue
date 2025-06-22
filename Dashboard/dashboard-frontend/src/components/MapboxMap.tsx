import React, { useRef, useEffect, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import './MapboxMap.css';
import 'mapbox-gl/dist/mapbox-gl.css';
import UserInfoCard from './UserInfoCard';
import HospitalInfo from './HospitalInfo';
import PoliceInfo from './PoliceInfo';
import ParamedicInfo from './ParamedicInfo';
import FireDepartmentInfo from './FireDepartmentInfo';
import { BadgeCheck, Flame, Hospital, HospitalIcon, Shield, Stethoscope } from "lucide-react";
import { AgentInfo, UserInfo } from '../types';
import { createRoot } from 'react-dom/client';

mapboxgl.accessToken = 'pk.eyJ1Ijoic2hhbnRhbnVraGFuYXB1cmUiLCJhIjoiY21hZnhjYTIzMDd3MDJqb2lyOWdveWVydyJ9.feVBjSgmBhBT2nFFubJ6PQ';

const CollapsibleCard = ({ title, children, icon }: { title: string, children: React.ReactNode, icon: React.ReactNode }) => {
  const [open, setOpen] = useState(true);
  return (
    <div className="bg-white/80 rounded-2xl shadow-lg border w-full">
      <button
        className="flex items-center justify-between w-full px-4 py-2 border-b border-gray-200 focus:outline-none"
        onClick={() => setOpen((o) => !o)}
        type="button"
      >
        <span className="text-sms font-semibold text-gray-800 flex items-center gap-2">
          {icon}
          {title}
        </span>
        <span className="text-gray-500">{open ? '−' : '+'}</span>
      </button>
      {open && <div className="px-2 pb-2 pt-2">{children}</div>}
    </div>
  );
};

const MapboxMap: React.FC = () => {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const markerRef = useRef<mapboxgl.Marker | null>(null);
  const userMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const agentMarkerRefs = useRef<{ [key: string]: mapboxgl.Marker | null }>({});
  const agentIntervalRefs = useRef<{ [key: string]: NodeJS.Timeout | null }>({});
  const mapRef = useRef<mapboxgl.Map | null>(null);

  // State for each agent type
  const [hospital, setHospital] = useState<AgentInfo | null>(null);
  const [police, setPolice] = useState<AgentInfo | null>(null);
  const [paramedic, setParamedic] = useState<AgentInfo | null>(null);
  const [fire, setFire] = useState<AgentInfo | null>(null);
  const [user, setUser] = useState<UserInfo | null>(null);

  // State to store SSE events
  const [events, setEvents] = useState<string[]>([]);
  // State for parsed event summaries
  const [eventSummaries, setEventSummaries] = useState<string[]>([]);
  // State for blinking cursor
  const [blink, setBlink] = useState(true);

  // Blinking cursor effect
  useEffect(() => {
    const interval = setInterval(() => setBlink((b) => !b), 500);
    return () => clearInterval(interval);
  }, []);

  // Listen to SSE events from backend and update agent states
  useEffect(() => {
    const evtSource = new EventSource('http://localhost:3000/events');
    evtSource.onmessage = (event) => {
      setEvents((prev) => [...prev, event.data]);
      try {
        const data = JSON.parse(event.data);
        // --- summary logic ---
        let summary = '';
        switch (data.type) {
          case 'hospital':
            summary = `Hospital dispatched: ${data.name || ''} (${data.address || ''})`;
            break;
          case 'police':
            summary = `Police dispatched: ${data.name || ''} (${data.address || ''})`;
            break;
          case 'paramedic':
            summary = `Paramedic dispatched: ${data.name || ''} (${data.address || ''})`;
            break;
          case 'fire':
            summary = `Fire Dept dispatched: ${data.name || ''} (${data.address || ''})`;
            break;
          case 'user':
            summary = `Caller: ${data.name || ''} (${data.location || ''})`;
            break;
          default:
            summary = `Event: ${event.data}`;
        }
        setEventSummaries((prev) => [...prev, summary]);
      } catch (e) {
        setEventSummaries((prev) => [...prev, `Event: ${event.data}`]);
      }
      try {
        const data = JSON.parse(event.data);
        switch (data.type) {
          case 'hospital':
            setHospital(data);
            break;
          case 'police':
            setPolice(data);
            break;
          case 'paramedic':
            setParamedic(data);
            break;
          case 'fire':
            setFire(data);
            break;
          case 'user':
            setUser(data);
            break;
          default:
            break;
        }
      } catch (e) {
        // fallback: ignore or log
      }
    };
    return () => evtSource.close();
  }, []);

  useEffect(() => {
    if (mapContainerRef.current) {
      const map = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: 'mapbox://styles/mapbox/dark-v11',
        center: [-74.5, 40],
        zoom: 15,
        pitch: 60,
        bearing: -17.6
      });
      mapRef.current = map;

      map.on('load', () => {
        // Add DEM terrain
        map.addSource('mapbox-dem', {
          type: 'raster-dem',
          url: 'mapbox://mapbox.mapbox-terrain-dem-v1',
          tileSize: 512,
          maxzoom: 14
        });
        map.setTerrain({ source: 'mapbox-dem', exaggeration: 1.5 });

        // Add built-in Mapbox 3D buildings
        map.addLayer({
          id: '3d-buildings',
          source: 'composite',
          'source-layer': 'building',
          filter: ['==', 'extrude', 'true'],
          type: 'fill-extrusion',
          minzoom: 15,
          paint: {
            'fill-extrusion-color': '#aaa',
            'fill-extrusion-height': [
              'interpolate',
              ['linear'],
              ['zoom'],
              15, 0,
              15.05, ['get', 'height']
            ],
            'fill-extrusion-base': [
              'interpolate',
              ['linear'],
              ['zoom'],
              15, 0,
              15.05, ['get', 'min_height']
            ],
            'fill-extrusion-opacity': 0.6
          }
        });

        // Use Geolocation API to get the user's current position
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition((position) => {
            const userLocation: [number, number] = [position.coords.longitude, position.coords.latitude];
            console.log('User location:', userLocation);

            // Center the map on the user's location
            map.flyTo({
              center: userLocation,
              zoom: 18,
              essential: true
            });
            // --- End of geolocation logic ---
          }, (error) => {
            console.error('Error getting location:', error);
          });
        } else {
          console.error('Geolocation is not supported by this browser.');
        }
      });

      return () => { map.remove(); mapRef.current = null; };
    }
  }, []);

  // Place or update the user marker when user state changes
  useEffect(() => {
    if (!user || !mapRef.current) return;
    const map = mapRef.current;
    // Remove previous user marker
    if (userMarkerRef.current) {
      userMarkerRef.current.remove();
    }
    // Place new user marker (blue)
    userMarkerRef.current = new mapboxgl.Marker({ color: 'blue' })
      .setLngLat([user.lon, user.lat])
      .addTo(map);
  }, [user]);

  // Place or animate agent markers when agent/user state changes
  useEffect(() => {
    if (!user || !mapRef.current) return;
    const map = mapRef.current;
    const agents = [
      { data: paramedic, color: 'red', type: 'paramedic' },
      { data: fire, color: 'orange', type: 'fire' },
      { data: police, color: 'indigo', type: 'police' }
    ];
    agents.forEach(({ data, color, type }) => {
      if (!data) return;
      // If marker exists, get its current position
      let startLngLat: [number, number] | null = null;
      if (agentMarkerRefs.current[type]) {
        const marker = agentMarkerRefs.current[type]!;
        const lngLat = marker.getLngLat();
        startLngLat = [lngLat.lng, lngLat.lat];
      }
      // If no marker or position changed, update
      const hasMoved = !startLngLat || startLngLat[0] !== data.lon || startLngLat[1] !== data.lat;
      if (!hasMoved) return; // Don't reset if not moved
      // Remove previous marker and interval if any
      if (agentMarkerRefs.current[type]) {
        agentMarkerRefs.current[type]?.remove();
        agentMarkerRefs.current[type] = null;
      }
      if (agentIntervalRefs.current[type]) {
        clearInterval(agentIntervalRefs.current[type]!);
        agentIntervalRefs.current[type] = null;
      }
      // Remove previous route layer and source if any
      if (map.getLayer(`${type}-route`)) {
        map.removeLayer(`${type}-route`);
      }
      if (map.getSource(`${type}-route`)) {
        map.removeSource(`${type}-route`);
      }
      // Place marker at current or new position
      const marker = new mapboxgl.Marker({ color })
        .setLngLat(startLngLat || [data.lon, data.lat])
        .addTo(map);
      agentMarkerRefs.current[type] = marker;
      // Animate marker to user
      const directionsUrl = `https://api.mapbox.com/directions/v5/mapbox/driving/${startLngLat ? startLngLat[0] : data.lon},${startLngLat ? startLngLat[1] : data.lat};${user.lon},${user.lat}?geometries=geojson&overview=full&access_token=${mapboxgl.accessToken}`;
      fetch(directionsUrl)
        .then(res => res.json())
        .then(routeData => {
          if (routeData.routes && routeData.routes.length > 0) {
            const route = routeData.routes[0].geometry;
            const routeCoords = route.coordinates;
            // Add the route as a source and layer (blue line)
            map.addSource(`${type}-route`, {
              type: 'geojson',
              data: {
                type: 'Feature',
                properties: {},
                geometry: route
              }
            });
            map.addLayer({
              id: `${type}-route`,
              type: 'line',
              source: `${type}-route`,
              layout: {
                'line-join': 'round',
                'line-cap': 'round'
              },
              paint: {
                'line-color': '#3b82f6',
                'line-width': 6
              }
            });
            let progress = 0;
            agentIntervalRefs.current[type] = setInterval(() => {
              progress++;
              if (progress < routeCoords.length) {
                marker.setLngLat(routeCoords[progress]);
              } else {
                marker.setLngLat(routeCoords[routeCoords.length - 1]);
                clearInterval(agentIntervalRefs.current[type]!);
                agentIntervalRefs.current[type] = null;
              }
            }, 500);
          }
        });
    });
  }, [paramedic, fire, police, user]);

  // Place or update the hospital marker when hospital state changes
  useEffect(() => {
    if (!hospital || !mapRef.current) return;
    const map = mapRef.current;

    // Remove previous hospital marker if any
    if (agentMarkerRefs.current['hospital']) {
      agentMarkerRefs.current['hospital']?.remove();
      agentMarkerRefs.current['hospital'] = null;
    }

    // Create a div for the custom marker
    const el = document.createElement('div');
    el.style.width = '36px';
    el.style.height = '36px';
    el.style.display = 'flex';
    el.style.alignItems = 'center';
    el.style.justifyContent = 'center';

    // Render the Lucide Hospital icon into the div
    const root = createRoot(el);
    root.render(<HospitalIcon color="#22c55e" size={32} />); // green color, 32px

    // Place the custom marker
    const marker = new mapboxgl.Marker(el)
      .setLngLat([hospital.lon, hospital.lat])
      .addTo(map);

    agentMarkerRefs.current['hospital'] = marker;
  }, [hospital]);

  // Create a separate component for the user information card

  // Use the UserInfoCard component in the main component
  const panels = [
    <UserInfoCard key={0} />, // Use the new component
    ...Array.from({ length: 3 }, (_, index) => (
      <div key={index + 1} className="info-panel">
        Panel {index + 1}
      </div>
    ))
  ];

  return (
    <div className="map-container" ref={mapContainerRef} style={{ width: '100%', height: '100vh', position: 'relative' }}>
      {/* Floating SSE debug panel as live terminal */}
      <div className="fixed bottom-4 left-4 z-50 bg-black/90 text-green-400 rounded-lg shadow-lg p-4 max-w-xl max-h-60 overflow-y-auto text-xs font-mono border border-green-700">
        <div className="font-bold text-green-300 mb-2 text-left"> Agent Actions (Live Terminal)</div>
        {eventSummaries.length === 0 ? (
          <div className="text-gray-500 text-left">Waiting for events <span className={blink ? '' : 'opacity-0'}>|</span></div>
        ) : (
          <>
            {eventSummaries.map((summary, i) => (
              <div key={i} className="mb-1 whitespace-pre-wrap break-all text-left">{summary}</div>
            ))}
            <div className="inline-block pl-1">
              <span className={blink ? '' : 'opacity-0'}>|</span>
            </div>
          </>
        )}
      </div>
      <div className="flex flex-col items-end gap-2 absolute top-4 right-4 z-50 w-[340px]">
        <CollapsibleCard title="Caller Information" icon={<BadgeCheck className="w-5 h-5 text-blue-600" />}>
          <UserInfoCard info={user} />
        </CollapsibleCard>
        <CollapsibleCard title="Fire Department Information" icon={<Flame className="w-5 h-5 text-orange-600" />}>
          <FireDepartmentInfo info={fire} />
        </CollapsibleCard>
        <CollapsibleCard title="Hospital Information" icon={<Hospital className="w-5 h-5 text-green-600" />}>
          <HospitalInfo info={hospital} />
        </CollapsibleCard>
        <CollapsibleCard title="Police Information" icon={<Shield className="w-5 h-5 text-indigo-600" />}>
          <PoliceInfo info={police} />
        </CollapsibleCard>
        <CollapsibleCard title="Paramedic Information" icon={<Stethoscope className="w-5 h-5 text-red-600" />}>
          <ParamedicInfo info={paramedic} />
        </CollapsibleCard>
      </div>
    </div>
  );
};

export default MapboxMap;