import React from "react";
import { Shield, MapPin, Phone, Ruler } from "lucide-react";
import { AgentInfo } from '../types';

interface PoliceInfoProps {
  info?: AgentInfo | null;
}

const PoliceInfo: React.FC<PoliceInfoProps> = ({ info }) => {
  if (!info) {
    return (
      <div className="flex items-center justify-center h-32">
        <button className="bg-indigo-600 text-white px-4 py-2 rounded font-semibold shadow hover:bg-indigo-700 transition">
          Take Action
        </button>
      </div>
    );
  }

  const police = info;
  return (
    <div>
      {/* Police Details aligned to the left */}
      <div className="space-y-2 text-gray-700 px-2 pb-2">
        <div className="flex items-center space-x-2">
          <Shield className="w-5 h-5 text-indigo-600" />
          <span className="font-medium">{police.name}</span>
        </div>
        <div className="flex items-center space-x-2">
          <MapPin className="w-5 h-5 text-indigo-600" />
          <span>{police.address}</span>
        </div>
        <div className="flex items-center space-x-2">
          <Ruler className="w-5 h-5 text-indigo-600" />
          <span>{police.distance}</span>
        </div>
        <div className="flex items-center space-x-2">
          <Phone className="w-5 h-5 text-indigo-600" />
          <span>{police.contact}</span>
        </div>
      </div>
    </div>
  );
};

export default PoliceInfo;
