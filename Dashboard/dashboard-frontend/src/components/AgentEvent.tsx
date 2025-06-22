import React, { useEffect, useState } from 'react';

function AgentEvents() {
  const [events, setEvents] = useState<string[]>([]);

  useEffect(() => {
    const evtSource = new EventSource('http://localhost:3000/events');
    evtSource.onmessage = (event) => {
      setEvents((prev) => [...prev, event.data]);
    };
    return () => evtSource.close();
  }, []);

  return (
    <div>
      <h2>Agent Events</h2>
      <pre>
        {events.map((e, i) => <div key={i}>{e}</div>)}
      </pre>
    </div>
  );
}

export default AgentEvents;