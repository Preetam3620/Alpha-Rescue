export interface AgentInfo {
  type: 'hospital' | 'police' | 'paramedic' | 'fire';
  name: string;
  address: string;
  distance: string;
  contact: string;
  lat: number;
  lon: number;
}

export interface UserInfo {
  type: 'user';
  name: string;
  location: string;
  phone: string;
  age: number;
  injuryStatus: string;
  lat: number;
  lon: number;
  transcript: string;
}

export type CardInfo = AgentInfo | UserInfo;
