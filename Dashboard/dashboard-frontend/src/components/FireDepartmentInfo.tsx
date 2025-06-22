import React from "react";
import { Flame, MapPin, Phone, Ruler } from "lucide-react";
import { AgentInfo } from '../types';

interface FireDepartmentInfoProps {
  info?: AgentInfo | null;
}

const FireDepartmentInfo: React.FC<FireDepartmentInfoProps> = ({ info }) => {
  if (!info) {
    return (
      <div className="flex items-center justify-center h-32">
        <button className="bg-orange-600 text-white px-4 py-2 rounded font-semibold shadow hover:bg-orange-700 transition">Take Action</button>
      </div>
    );
  }

  const fireDept = info;
  return (
    <div>
      {/* Fire Department Details aligned to the left */}
      <div className="space-y-2 text-gray-700 px-2 pb-2">
        <div className="flex items-center space-x-2">
          <Flame className="w-5 h-5 text-orange-600" />
          <span className="font-medium">{fireDept.name}</span>
        </div>
        <div className="flex items-center space-x-2">
          <MapPin className="w-5 h-5 text-orange-600" />
          <span>{fireDept.address}</span>
        </div>
        <div className="flex items-center space-x-2">
          <Ruler className="w-5 h-5 text-orange-600" />
          <span>{fireDept.distance}</span>
        </div>
        <div className="flex items-center space-x-2">
          <Phone className="w-5 h-5 text-orange-600" />
          <span>{fireDept.contact}</span>
        </div>
      </div>
    </div>
  );
};

export default FireDepartmentInfo;
