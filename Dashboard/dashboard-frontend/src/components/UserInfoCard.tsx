import React from "react";
import { BadgeCheck, Phone, MapPin, Calendar, HeartPulse } from "lucide-react";
import { UserInfo } from '../types';

interface UserInfoCardProps {
  info?: UserInfo | null;
}

const UserInfoCard: React.FC<UserInfoCardProps> = ({ info }) => {
  if (!info) {
    return (
      <div className="flex items-center justify-center h-32">
        <button className="bg-blue-600 text-white px-4 py-2 rounded font-semibold shadow hover:bg-blue-700 transition">
          No Active Case
        </button>
      </div>
    );
  }

  const userInfo = info;
  return (
    <div>
      {/* User Details aligned to the left */}
      <div className="space-y-2 text-gray-700 px-2 pb-2">
        <div className="flex items-center space-x-2">
          <BadgeCheck className="w-5 h-5 text-blue-600" />
          <span className="font-medium">{userInfo.name}</span>
        </div>
        <div className="flex items-center space-x-2">
          <MapPin className="w-5 h-5 text-blue-600" />
          <span>{userInfo.location}</span>
        </div>
        <div className="flex items-center space-x-2">
          <Phone className="w-5 h-5 text-blue-600" />
          <span>{userInfo.phone}</span>
        </div>
        <div className="flex items-center space-x-2">
          <Calendar className="w-5 h-5 text-blue-600" />
          <span>Age: {userInfo.age}</span>
        </div>
        <div className="flex items-center space-x-2">
          <HeartPulse className="w-5 h-5 text-blue-600" />
          <span>{userInfo.transcript}</span>
        </div>
      </div>
    </div>
  );
};

export default UserInfoCard;
