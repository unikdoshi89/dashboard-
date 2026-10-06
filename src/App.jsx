import {
  Routes,
  Route,
} from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import AutomationDetails from "./pages/AutomationDetails";
import JiraDetails from "./pages/JiraDetails";
import CalculationDetails from "./pages/CalculationDetails";


function App() {
  return (
    <Routes>

      <Route
        path="/"
        element={<Dashboard />}
      />

      <Route
        path="/automation/:projectId"
        element={<AutomationDetails />}
      />

      <Route
        path="/jira/:projectId"
        element={<JiraDetails />}
      />

      <Route
  path="/calculation-details/:projectId"
  element={<CalculationDetails />}
/>

    </Routes>

  );
}

export default App;
