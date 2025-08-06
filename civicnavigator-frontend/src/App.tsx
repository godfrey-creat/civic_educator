import { useState } from "react";
import ChatInterface from "./components/ChatInterface";
import IncidentForm from "./components/IncidentForm";
import StatusLookup from "./components/StatusLookup";
import StaffTools from "./components/StaffTools";
import RoleToggle from "./components/RoleToggle";

function App() {
  const [role, setRole] = useState<"resident" | "staff">("resident");

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6 text-center">CivicNavigator</h1>

      <RoleToggle role={role} onChange={setRole} />

      <ChatInterface role={role} />

      {role === "resident" && (
        <>
          <IncidentForm />
          <StatusLookup />
        </>
      )}

      {role === "staff" && <StaffTools />}
    </div>
  );
}

export default App;
