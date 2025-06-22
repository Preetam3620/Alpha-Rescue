import React from "react";
import { Hospital, MapPin, Phone, Ruler } from "lucide-react";
import { AgentInfo } from '../types';

interface HospitalInfoProps {
  info?: AgentInfo | null;
}

const HospitalInfo: React.FC<HospitalInfoProps> = ({ info }) => {
  if (!info) {
    return (
      <div className="flex items-center justify-center h-32">
        <button className="bg-green-600 text-white px-4 py-2 rounded font-semibold shadow hover:bg-green-700 transition">Take Action</button>
      </div>
    );
  }

  const hospital = info;
  return (
    <div>
      {/* Hospital Details aligned to the left */}
      <div className="space-y-2 text-gray-700 px-2 pb-2">
        <div className="flex items-center space-x-2">
          <Hospital className="w-5 h-5 text-green-600" />
          <span className="font-medium">{hospital.name}</span>
        </div>
        <div className="flex items-center space-x-2">
          <MapPin className="w-5 h-5 text-green-600" />
          <span>{hospital.address}</span>
        </div>
        <div className="flex items-center space-x-2">
          <Ruler className="w-5 h-5 text-green-600" />
          <span>{hospital.distance}</span>
        </div>
        <div className="flex items-center space-x-2">
          <Phone className="w-5 h-5 text-green-600" />
          <span>{hospital.contact}</span>
        </div>
      </div>
    </div>
  );
};

export default HospitalInfo;