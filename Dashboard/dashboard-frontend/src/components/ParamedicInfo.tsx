import React from "react";
import { Stethoscope, MapPin, Phone, Ruler } from "lucide-react";
import { AgentInfo } from '../types';

interface ParamedicInfoProps {
  info?: AgentInfo | null;
}

const ParamedicInfo: React.FC<ParamedicInfoProps> = ({ info }) => {
  if (!info) {
    return (
      <div className="flex items-center justify-center h-32">
        <button className="bg-red-600 text-white px-4 py-2 rounded font-semibold shadow hover:bg-red-700 transition">Take Action</button>
      </div>
    );
  }

  const paramedic = info;
  return (
    <div>
      {/* Paramedic Details aligned to the left */}
      <div className="space-y-2 text-gray-700 px-2 pb-2">
        <div className="flex items-center space-x-2">
          <Stethoscope className="w-5 h-5 text-red-600" />
          <span className="font-medium">{paramedic.name}</span>
        </div>
        <div className="flex items-center space-x-2">
          <MapPin className="w-5 h-5 text-red-600" />
          <span>{paramedic.address}</span>
        </div>
        <div className="flex items-center space-x-2">
          <Ruler className="w-5 h-5 text-red-600" />
          <span>{paramedic.distance}</span>
        </div>
        <div className="flex items-center space-x-2">
          <Phone className="w-5 h-5 text-red-600" />
          <span>{paramedic.contact}</span>
        </div>
      </div>
    </div>
  );
};

export default ParamedicInfo;
