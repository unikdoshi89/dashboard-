import {
  useEffect,
  useState
} from "react";

import {
  Plus,
  ArrowRight,
  Activity,
  ShieldCheck,
  Target,
  TrendingUp,
  Download,
  Calculator
} from "lucide-react";

import {
  Link,
  useNavigate,
  useParams,
  useSearchParams
} from "react-router-dom";


import {
  getProjects,
  getProjectDashboard,
  createProject,
  getAvailableMetrics,
  addMetric,
  getQualityScore,
  downloadProjectPdf,
} from "../api/projects";

import {
  updateMetricValue,
} from "../api/metrics";


import ProjectSelector from "../components/ProjectSelector";
import AddProjectModal from "../components/AddProjectModal";
import AddMetricModal from "../components/AddMetricModal";
import QualityScoreCard from "../components/QualityScoreCard";

function Dashboard() {
  const navigate = useNavigate();

  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showDetailsMenu, setShowDetailsMenu] = useState(false);

  const [showAddProject, setShowAddProject] = useState(false);
  const [showAddMetric, setShowAddMetric] = useState(false);
  const [qualityScore, setQualityScore] = useState(null);
  const [editingMetricId, setEditingMetricId] =
  useState(null);

const [editValue, setEditValue] =
  useState("");

const [editNotes, setEditNotes] =
  useState("");

const [updatingMetric, setUpdatingMetric] =
  useState(false);
const [qualityScoreLoading, setQualityScoreLoading] =
  useState(false);

  const [availableMetrics, setAvailableMetrics] = useState([]);
  const [
  searchParams
] = useSearchParams();




  // ==================================================
  // Load Projects
  // ==================================================

  useEffect(() => {
    async function loadProjects() {
      try {
        setError("");

        const data = await getProjects();

        setProjects(data);

        if (data.length > 0) {
          setSelectedProjectId(data[0].id);
        }
      } catch (err) {
        console.error("Failed to load projects:", err);

        setError(
          err.response?.data?.detail ||
          "Failed to load projects"
        );
      }
    }

    loadProjects();
  }, []);


  // ==================================================
  // Load Dashboard
  // ==================================================

  useEffect(() => {
    if (!selectedProjectId) {
      return;
    }

    async function loadDashboard() {
      try {
        setLoading(true);
        setError("");

        const data = await getProjectDashboard(
          selectedProjectId
        );

        setDashboard(data);
      } catch (err) {
        console.error(
          "Failed to load dashboard:",
          err
        );

        setError(
          err.response?.data?.detail ||
          "Failed to load dashboard"
        );
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, [selectedProjectId]);


  // ==================================================
  // Load Available Metrics
  // ==================================================

  useEffect(() => {
    if (!selectedProjectId) {
      return;
    }

    async function loadAvailableMetrics() {
      try {
        const data = await getAvailableMetrics(
          selectedProjectId
        );

        setAvailableMetrics(data);
      } catch (err) {
        console.error(
          "Failed to load available metrics:",
          err
        );
      }
    }

    loadAvailableMetrics();
  }, [selectedProjectId, dashboard]);



async function handleUpdateMetric(metric) {
  try {
    setUpdatingMetric(true);
    setError("");

    await updateMetricValue(
      metric.project_metric_id,
      {
        value: Number(editValue),
        notes: editNotes,
        updated_by: "current-user",
      }
    );

    // Reload dashboard
    const data = await getProjectDashboard(
      selectedProjectId
    );

    setDashboard(data);

    // Reload quality score
    const scoreData = await getQualityScore(
      selectedProjectId
    );

    setQualityScore(scoreData);

    // Exit edit mode
    setEditingMetricId(null);
    setEditValue("");
    setEditNotes("");

  } catch (err) {
    console.error(
      "Failed to update metric:",
      err
    );

    setError(
      err.response?.data?.detail ||
      "Failed to update metric"
    );

  } finally {
    setUpdatingMetric(false);
  }
}

function handleEditMetric(metric) {
  setEditingMetricId(
    metric.project_metric_id
  );

  setEditValue(
    metric.value ?? ""
  );

  setEditNotes(
    metric.notes ?? ""
  );

  setError("");
}
function handleCancelEdit() {
  setEditingMetricId(null);
  setEditValue("");
  setEditNotes("");
}

  useEffect(() => {
  if (!selectedProjectId) {
    setQualityScore(null);
    return;
  }

  async function loadQualityScore() {
    try {
      setQualityScoreLoading(true);

      const data = await getQualityScore(
        selectedProjectId
      );

      setQualityScore(data);
    } catch (err) {
      console.error(
        "Failed to load quality score:",
        err
      );

      setQualityScore(null);
    } finally {
      setQualityScoreLoading(false);
    }
  }

  loadQualityScore();
}, [selectedProjectId]);


  // ==================================================
  // Project Change
  // ==================================================

  function handleProjectChange(projectId) {
    setSelectedProjectId(Number(projectId));
  }


  // ==================================================
  // Add Metric
  // ==================================================

  async function handleAddMetric(metricData) {
    try {
      setError("");

      console.log(
        "Adding metric:",
        metricData
      );

      await addMetric(
        selectedProjectId,
        metricData
      );

      setShowAddMetric(false);

      const data = await getProjectDashboard(
        selectedProjectId
      );

      setDashboard(data);
    } catch (err) {
      console.error(
        "Failed to add metric:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Failed to add metric"
      );
    }
  }


  // ==================================================
  // Add Project
  // ==================================================

  async function handleCreateProject(projectData) {
    try {
      setError("");

      const newProject =
        await createProject(projectData);

      setProjects((previous) => [
        ...previous,
        newProject,
      ]);

      setSelectedProjectId(
        newProject.id
      );

      setShowAddProject(false);
    } catch (err) {
      console.error(
        "Failed to create project:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Failed to create project"
      );
    }
  }

async function handleDownloadPdf() {
  if (!selectedProjectId) {
    return;
  }

  try {
    setError("");

    const blob = await downloadProjectPdf(
      selectedProjectId
    );

    const url =
      window.URL.createObjectURL(blob);

    const link =
      document.createElement("a");

    link.href = url;

    const projectName =
      dashboard?.project?.name ||
      "project";

    link.download =
      `QE_Governance_${projectName.replace(
        /\s+/g,
        "_"
      )}.pdf`;

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);

    window.URL.revokeObjectURL(url);

  } catch (err) {

    console.error(
      "Failed to download PDF:",
      err
    );

    setError(
      err.response?.data?.detail ||
      "Failed to generate PDF"
    );
  }
}

  // ==================================================
  // Open Automation
  // ==================================================

  function openAutomation() {

  if (!selectedProjectId) {
    return;
  }

  navigate(
    `/automation/${selectedProjectId}`
  );
}

useEffect(() => {

  async function loadProjects() {

    try {

      setError("");

      const data =
        await getProjects();

      setProjects(data);


      if (data.length > 0) {

        const projectFromUrl =
          Number(
            searchParams.get("project")
          );


        const projectExists =
          data.some(
            (project) =>
              project.id ===
              projectFromUrl
          );


        if (projectExists) {

          setSelectedProjectId(
            projectFromUrl
          );

        } else {

          setSelectedProjectId(
            data[0].id
          );

        }

      }

    } catch (err) {

      console.error(
        "Failed to load projects:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Failed to load projects"
      );

    }

  }

  loadProjects();

}, []);


  // ==================================================
  // Render
  // ==================================================

  return (
    <div className="min-h-screen bg-gray-50">

      {/* ==================================================
          HEADER
          ================================================== */}

      <header className="bg-white border-b border-gray-200">

        <div className="max-w-7xl mx-auto px-6 py-4">

          <div className="flex items-center justify-between gap-6">

            {/* Application Name */}

            <div>
              <h1 className="text-xl font-bold text-gray-900">
                QE Governance
              </h1>

              <p className="text-sm text-gray-500 mt-1">
                Quality Engineering Dashboard
              </p>
            </div>


            {/* Header Controls */}

            <div className="flex items-center gap-3">

{/*               <button */}
{/*   type="button" */}
{/*   onClick={openAutomation} */}
{/*   className="hidden md:inline-flex items-center gap-2 px-4 py-2.5 bg-blue-50 text-blue-700 border border-blue-200 rounded-lg text-sm font-medium hover:bg-blue-100" */}
{/* > */}
{/*   Automation Details */}
{/*   <ArrowRight size={16} /> */}
{/* </button> */}


              <ProjectSelector
                projects={projects}
                selectedProjectId={
                  selectedProjectId
                }
                onChange={
                  handleProjectChange
                }
              />


              <button
                type="button"
                onClick={() =>
                  setShowAddProject(true)
                }
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
              >
                <Plus size={16} />

                <span className="hidden sm:inline">
                  Add Project
                </span>
              </button>

            </div>

          </div>

        </div>

      </header>


      {/* ==================================================
          MAIN
          ================================================== */}

      <main className="max-w-7xl mx-auto px-6 py-8">


        {/* Error */}

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
            {error}
          </div>
        )}


        {/* Loading */}

        {loading && (
          <div className="text-center py-16 text-gray-500">
            Loading dashboard...
          </div>
        )}


        {/* Dashboard */}

        {!loading && dashboard && (
          <div>


            {/* ==================================================
                PROJECT HEADER
                ================================================== */}

            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl p-6 mb-8 shadow-md">

              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-5">

                {/* Project Information */}

                <div>

                  <h2 className="text-2xl font-bold">
                    {dashboard.project.name}
                  </h2>

                  <p className="text-blue-100 mt-1">
                    {dashboard.project.project_key}
                  </p>

                </div>


                {/* Actions */}

                <div className="flex items-center gap-3">

{/*                   <button */}
{/*                     type="button" */}
{/*                     onClick={openAutomation} */}
{/*                     className="inline-flex items-center gap-2 px-4 py-2.5 bg-white text-blue-700 rounded-lg text-sm font-semibold hover:bg-blue-50 shadow-sm" */}
{/*                   > */}
{/*                     Automation Details */}
{/*                     <ArrowRight size={16} /> */}
{/*                   </button> */}
                      <div className="relative">

  <button
    type="button"
    onClick={() => setShowDetailsMenu((prev) => !prev)}
    disabled={!selectedProjectId}
    className="inline-flex items-center gap-2 px-4 py-2.5 bg-white text-blue-700 rounded-lg text-sm font-semibold hover:bg-blue-50 shadow-sm disabled:opacity-50"
  >
    Open Details
    <ArrowRight size={16} />
  </button>


  {showDetailsMenu && selectedProjectId && (
    <div className="absolute right-0 mt-2 w-52 bg-white border border-gray-200 rounded-lg shadow-lg z-50">

      <button
        type="button"
        onClick={() => {
          setShowDetailsMenu(false);
          navigate(`/automation/${selectedProjectId}`);
        }}
        className="w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-gray-50"
      >
        Automation Details
      </button>


      <button
        type="button"
        onClick={() => {
          setShowDetailsMenu(false);
          navigate(`/jira/${selectedProjectId}`);
        }}
        className="w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-gray-50"
      >
        Jira Details
      </button>

      <button
        type="button"
        onClick={() => {
          setShowDetailsMenu(false);
          navigate(`/calculation-details/${selectedProjectId}`);
        }}
        className="w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-gray-50"
      >
        Calculation Details
      </button>

    </div>
  )}

</div>


{/*                   <div className="hidden lg:block px-4 py-2.5 bg-white/15 rounded-lg text-sm font-medium"> */}
{/*                     QE Governance */}
{/*                   </div> */}

                  <button
    onClick={handleDownloadPdf}
    disabled={!selectedProjectId}
    className="
      inline-flex
      items-center
      gap-2
      px-4
      py-2.5
      bg-white
      text-blue-700
      rounded-lg
      text-sm
      font-semibold
      hover:bg-blue-50
      transition-colors
      shadow-sm
      disabled:opacity-50
      disabled:cursor-not-allowed
    "
  >
    <Download size={17} />
    Download PDF
  </button>

                  <button
                    type="button"
                    onClick={() =>
                      setShowAddMetric(true)
                    }
                    className="inline-flex items-center gap-2 px-4 py-2.5 bg-white text-blue-700 rounded-lg text-sm font-semibold hover:bg-blue-50 shadow-sm"
                  >
                    <Plus size={17} />
                    Add Metric
                  </button>

                </div>

              </div>

            </div>

            <QualityScoreCard
      qualityScore={qualityScore}
      loading={qualityScoreLoading}
    />

            {/* ==================================================
                CATEGORIES
                ================================================== */}

            <div className="space-y-10">

              {dashboard.categories.map(
                (category) => (
                  <section
                    key={category.category_id}
                  >

                    {/* Category Header */}

                    <div className="flex items-center gap-3 mb-4">

                      <div className="w-1 h-7 bg-blue-600 rounded-full flex-shrink-0"></div>

                      <h3 className="text-xl font-semibold text-gray-900">
                        {category.category_name}
                      </h3>

                    </div>


                    {/* ==================================================
                        METRICS
                        ================================================== */}

                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">

                      {category.metrics.map(
                        (metric) => {

                          const isAutomationCoverage =
                            metric.metric_key ===
                              "automation_coverage" ||
                            metric.name ===
                              "Automation Coverage %";


                          return (
                            <div
  key={
    metric.project_metric_id
  }
  onClick={() => {
    if (
      isAutomationCoverage &&
      editingMetricId !== metric.project_metric_id
    ) {
      openAutomation();
    }
  }}
                              className={
                                isAutomationCoverage
                                  ? "bg-white border border-gray-200 rounded-xl p-5 shadow-sm cursor-pointer hover:shadow-lg hover:border-blue-300 transition-all"
                                  : "bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-all"
                              }
                            >

                              {/* Metric information */}

                              <div className="flex justify-between gap-4">

                                <div>

                                  <h4 className="font-semibold text-gray-900">
                                    {metric.name}
                                  </h4>

                                  <p className="text-sm text-gray-500 mt-1">
                                    {metric.description}
                                  </p>

                                </div>


                                {editingMetricId === metric.project_metric_id ? (
  <div
    className="flex items-center gap-2"
    onClick={(event) =>
      event.stopPropagation()
    }
  >
    <input
      type="number"
      value={editValue}
      onChange={(event) =>
        setEditValue(event.target.value)
      }
      className="w-24 px-3 py-2 border border-gray-300 rounded-lg text-right text-lg font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500"
    />

    <span className="text-gray-600">
      {metric.unit}
    </span>
  </div>
) : (
  <div className="text-2xl font-bold text-blue-600 whitespace-nowrap">
    {metric.value}
    {metric.unit}
  </div>
)}

                              </div>


                              {/* Automation link */}

                              {isAutomationCoverage && (
                                <div className="mt-3 text-xs text-blue-600 font-medium flex items-center gap-1">
                                  View Automation Details
                                  <ArrowRight size={13} />
                                </div>
                              )}

                              {editingMetricId === metric.project_metric_id ? (
  <div
    className="mt-4"
    onClick={(event) =>
      event.stopPropagation()
    }
  >
    <label className="block text-xs font-medium text-gray-600 mb-1">
      Notes
    </label>

    <input
      type="text"
      value={editNotes}
      onChange={(event) =>
        setEditNotes(event.target.value)
      }
      placeholder="Add notes"
      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
    />

    <div className="flex justify-end gap-2 mt-3">

      <button
        type="button"
        onClick={handleCancelEdit}
        disabled={updatingMetric}
        className="px-3 py-2 text-sm font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
      >
        Cancel
      </button>

      <button
        type="button"
        onClick={() =>
          handleUpdateMetric(metric)
        }
        disabled={
          updatingMetric ||
          editValue === ""
        }
        className="px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {updatingMetric
          ? "Updating..."
          : "Update"}
      </button>

    </div>
  </div>
) : (
  <div
    className="mt-4 flex justify-end"
    onClick={(event) =>
      event.stopPropagation()
    }
  >
    <button
      type="button"
      onClick={() =>
        handleEditMetric(metric)
      }
      className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50"
    >
      Edit
    </button>
  </div>
)}


                              {/* Footer */}

                              <div className="mt-5 pt-4 border-t border-gray-100 flex justify-between text-xs text-gray-500">

                                <span>
                                  Target:{" "}
                                  <strong>
                                    {metric.target}
                                    {metric.unit}
                                  </strong>
                                </span>

                                <span>
                                  Status:{" "}
                                  <strong>
                                    {metric.status}
                                  </strong>
                                </span>

                              </div>

                            </div>
                          );
                        }
                      )}

                    </div>

                  </section>
                )
              )}

            </div>

          </div>
        )}

      </main>


      {/* ==================================================
          ADD PROJECT MODAL
          ================================================== */}

      <AddProjectModal
        open={showAddProject}
        onClose={() =>
          setShowAddProject(false)
        }
        onSave={
          handleCreateProject
        }
      />


      {/* ==================================================
          ADD METRIC MODAL
          ================================================== */}

      <AddMetricModal
        open={showAddMetric}
        metrics={availableMetrics}
        onClose={() =>
          setShowAddMetric(false)
        }
        onSave={
          handleAddMetric
        }
      />

    </div>
  );
}


export default Dashboard;
