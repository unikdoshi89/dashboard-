import { useEffect, useState } from "react";
import {
  ArrowLeft,
  CheckCircle,
  ExternalLink,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import TagInput from "../components/TagInput";

import {
  getJiraConfig,
  saveJiraConfig,
  testJiraConnection,
  getJiraBugs,
  getJiraFeatures,
} from "../api/jira";


function JiraDetails() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  // ============================================================
  // Configuration
  // ============================================================

  const [jiraUrl, setJiraUrl] = useState("");
  const [jiraEmail, setJiraEmail] = useState("");
  const [jiraApiToken, setJiraApiToken] = useState("");
  const [jql, setJql] = useState("");
  const [featureJql, setFeatureJql] = useState("");

  const [uatLabels, setUatLabels] = useState([]);
  const [prodLabels, setProdLabels] = useState([]);

  const [active, setActive] = useState(true);
  const [configured, setConfigured] = useState(false);
  const [hasApiToken, setHasApiToken] = useState(false);

  // ============================================================
  // UI state
  // ============================================================

  const [loadingConfig, setLoadingConfig] = useState(true);
  const [savingConfig, setSavingConfig] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);

  const [configMessage, setConfigMessage] = useState("");
  const [configError, setConfigError] = useState("");

  // ============================================================
  // Jira issues
  // ============================================================

  const [bugs, setBugs] = useState([]);
  const [uatBugs, setUatBugs] = useState([]);
  const [prodBugs, setProdBugs] = useState([]);

  const [loadingBugs, setLoadingBugs] = useState(false);
  const [bugsError, setBugsError] = useState("");

  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState("all");

  const [features, setFeatures] = useState([]);
  const [loadingFeatures, setLoadingFeatures] = useState(false);
  const [featurePage, setFeaturePage] = useState(1);
  const [featurePerPage] = useState(20);
  const [featureTotal, setFeatureTotal] = useState(0);
  const [featurePages, setFeaturePages] = useState(1);
  const [featureSearch, setFeatureSearch] = useState("");
  const [featureError, setFeatureError] = useState("");


  // ============================================================
  // Load Jira configuration
  // ============================================================

  useEffect(() => {
    loadConfig();
  }, [projectId]);

  async function loadConfig() {
    try {
      setLoadingConfig(true);
      setConfigError("");
      setConfigMessage("");

      const data = await getJiraConfig(projectId);

      setConfigured(Boolean(data.configured));

      setJiraUrl(data.jira_url || "");
      setJiraEmail(data.jira_email || "");
      setJql(data.jql || "");
      setFeatureJql(data.feature_jql || "");

      setUatLabels(
  (data.uat_label || "")
    .split(",")
    .map(l => l.trim())
    .filter(l => l !== "")
);

setProdLabels(
  (data.prod_label || "")
    .split(",")
    .map(l => l.trim())
    .filter(l => l !== "")
);

      setActive(
        data.active !== undefined
          ? data.active
          : true
      );

      setHasApiToken(
        Boolean(data.has_api_token)
      );

    } catch (err) {
      console.error(
        "Unable to load Jira configuration:",
        err
      );

      setConfigError(
        err?.response?.data?.detail ||
        "Unable to load Jira configuration."
      );
    } finally {
      setLoadingConfig(false);
    }
  }

  // ============================================================
  // Load Jira bugs
  // ============================================================

  async function loadFeatures(searchValue = featureSearch) {
    try {
      setLoadingFeatures(true);
      setFeatureError("");

      const data = await getJiraFeatures(
        projectId,
        featurePage,
        featurePerPage,
        searchValue
      );

      if (!data.configured) {
        setFeatures([]);
        setFeatureTotal(0);
        setFeaturePages(1);
        return;
      }

      setFeatures(data.features || []);
      setFeatureTotal(data.total || 0);
      setFeaturePages(data.pages || 1);
    } catch (err) {
      console.error("Unable to load Jira features:", err);
      setFeatureError(
        err?.response?.data?.detail ||
        "Unable to fetch Jira features/stories."
      );
      setFeatures([]);
      setFeatureTotal(0);
      setFeaturePages(1);
    } finally {
      setLoadingFeatures(false);
    }
  }

useEffect(() => {
  loadFeatures();
}, [featurePage]);

  async function loadBugs(searchValue = search) {
    try {
      setLoadingBugs(true);
      setBugsError("");

      const data = await getJiraBugs(
        projectId,
        searchValue
      );

      if (!data.configured) {
        setBugs([]);
        setUatBugs([]);
        setProdBugs([]);
        setConfigured(false);
        return;
      }

      setConfigured(true);

      setBugs(data.bugs || []);
      setUatBugs(data.uat_bugs || []);
      setProdBugs(data.prod_bugs || []);

    } catch (err) {
      console.error(
        "Unable to load Jira bugs:",
        err
      );

      setBugsError(
        err?.response?.data?.detail ||
        "Unable to fetch Jira issues."
      );

      setBugs([]);
      setUatBugs([]);
      setProdBugs([]);

    } finally {
      setLoadingBugs(false);
    }
  }

  // ============================================================
  // Save Jira configuration
  // ============================================================

  async function handleSaveConfig() {
    try {
      setSavingConfig(true);
      setConfigError("");
      setConfigMessage("");

      if (!jiraUrl.trim()) {
        setConfigError(
          "Jira URL is required."
        );
        return;
      }

      if (!jiraEmail.trim()) {
        setConfigError(
          "Jira email is required."
        );
        return;
      }

      if (!jql.trim()) {
        setConfigError(
          "Bug JQL is required."
        );
        return;
      }

      if (!featureJql.trim()) {
        setConfigError(
          "Feature/Story JQL is required."
        );
        return;
      }

      if (uatLabels.length === 0) {
  setConfigError("At least one UAT issue label is required.");
  return;
}

if (prodLabels.length === 0) {
  setConfigError("At least one Production issue label is required.");
  return;
}

      if (
        !configured &&
        !jiraApiToken.trim()
      ) {
        setConfigError(
          "Jira API token is required."
        );
        return;
      }

      const payload = {
        jira_url: jiraUrl.trim(),
        jira_email: jiraEmail.trim(),
        jira_api_token:
          jiraApiToken.trim(),
        jql: jql.trim(),
        feature_jql: featureJql.trim(),
        uat_label: uatLabels.join(","),
        prod_label: prodLabels.join(","),
        active,
      };

      const data = await saveJiraConfig(
        projectId,
        payload
      );

      setConfigured(true);

      setHasApiToken(
        Boolean(data.has_api_token)
      );

      // Never keep the actual token in UI
      setJiraApiToken("");

      setConfigMessage(
        "Jira configuration saved successfully."
      );

      // Load Jira issues after saving
      await loadBugs("");
      setFeatureSearch("");
      setFeaturePage(1);
      await loadFeatures("");

    } catch (err) {
      console.error(
        "Unable to save Jira configuration:",
        err
      );

      setConfigError(
        err?.response?.data?.detail ||
        "Unable to save Jira configuration."
      );

    } finally {
      setSavingConfig(false);
    }
  }

  // ============================================================
  // Test Jira connection
  // ============================================================

  async function handleTestConnection() {
    try {
      setTestingConnection(true);
      setConfigError("");
      setConfigMessage("");

      const data =
        await testJiraConnection(
          projectId
        );

      setConfigMessage(
        data.message ||
        "Jira connection successful."
      );

    } catch (err) {
      console.error(
        "Unable to connect to Jira:",
        err
      );

      setConfigError(
        err?.response?.data?.detail ||
        "Unable to connect to Jira."
      );

    } finally {
      setTestingConnection(false);
    }
  }

  // ============================================================
  // Search
  // ============================================================

  async function handleSearch(event) {
    event.preventDefault();

    await loadBugs(search);
  }

  function handleClearSearch() {
    setSearch("");
    loadBugs("");
  }

  async function handleFeatureSearch(event) {
    event.preventDefault();
    setFeaturePage(1);
    await loadFeatures(featureSearch);
  }

  async function handleClearFeatureSearch() {
    setFeatureSearch("");
    setFeaturePage(1);
    await loadFeatures("");
  }

  // ============================================================
  // Refresh
  // ============================================================

  async function handleRefresh() {
    await loadConfig();

    if (configured) {
      await loadBugs(search);
    }
  }

  // ============================================================
  // Visible bugs
  // ============================================================

  const visibleBugs =
    activeTab === "uat"
      ? uatBugs
      : activeTab === "prod"
        ? prodBugs
        : bugs;

  // ============================================================
  // Helpers
  // ============================================================

  function formatDate(value) {
    if (!value) {
      return "-";
    }

    try {
      return new Date(value).toLocaleString();
    } catch {
      return value;
    }
  }

  function getStatusClass(status) {
    const normalized =
      String(status || "")
        .toLowerCase();

    if (
      normalized.includes("done") ||
      normalized.includes("closed") ||
      normalized.includes("resolved")
    ) {
      return "bg-green-100 text-green-700";
    }

    if (
      normalized.includes("progress") ||
      normalized.includes("open")
    ) {
      return "bg-blue-100 text-blue-700";
    }

    if (
      normalized.includes("blocked") ||
      normalized.includes("reopen")
    ) {
      return "bg-red-100 text-red-700";
    }

    return "bg-gray-100 text-gray-700";
  }

  function getPriorityClass(priority) {
    const normalized =
      String(priority || "")
        .toLowerCase();

    if (
      normalized.includes("highest") ||
      normalized.includes("critical") ||
      normalized.includes("blocker")
    ) {
      return "bg-red-100 text-red-700";
    }

    if (
      normalized.includes("high")
    ) {
      return "bg-orange-100 text-orange-700";
    }

    if (
      normalized.includes("medium")
    ) {
      return "bg-yellow-100 text-yellow-700";
    }

    return "bg-gray-100 text-gray-700";
  }

  function getJiraIssueUrl(jiraId) {
    if (!jiraUrl || !jiraId) {
      return "#";
    }

    return `${jiraUrl.replace(
      /\/$/,
      ""
    )}/browse/${jiraId}`;
  }

  // ============================================================
  // Loading configuration
  // ============================================================

  if (loadingConfig) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center gap-3 text-gray-600">
          <RefreshCw
            size={20}
            className="animate-spin"
          />
          Loading Jira configuration...
        </div>
      </div>
    );
  }

  // ============================================================
  // Page
  // ============================================================

  return (
    <div className="min-h-screen bg-gray-50">

      {/* ======================================================
          Header
      ======================================================= */}

      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-5">

          <div className="flex items-center justify-between">

            <div className="flex items-center gap-4">

              <button
                type="button"
                onClick={() => navigate("/")}
                className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
                title="Back to Dashboard"
              >
                <ArrowLeft size={20} />
              </button>

              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Jira Details
                </h1>

                <p className="text-sm text-gray-500 mt-1">
                  Jira configuration and issue tracking
                </p>
              </div>

            </div>

            <button
              type="button"
              onClick={handleRefresh}
              disabled={
                loadingBugs ||
                loadingConfig
              }
              className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              <RefreshCw
                size={16}
                className={
                  loadingBugs
                    ? "animate-spin"
                    : ""
                }
              />
              Refresh
            </button>

          </div>

        </div>
      </div>


      <div className="max-w-7xl mx-auto px-6 py-6">

        {/* ====================================================
            Configuration Card
        ===================================================== */}

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">

          <div className="px-6 py-4 border-b border-gray-200 flex items-center gap-3">

            <div className="p-2 bg-blue-50 rounded-lg">
              <Settings
                size={20}
                className="text-blue-600"
              />
            </div>

            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Jira Configuration
              </h2>

              <p className="text-sm text-gray-500">
                Configure Jira access and environment labels for this project.
              </p>
            </div>

          </div>


          <div className="p-6">

            {/* Configuration messages */}

            {configMessage && (
              <div className="mb-5 flex items-center gap-2 rounded-lg bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-700">
                <CheckCircle size={18} />
                {configMessage}
              </div>
            )}

            {configError && (
              <div className="mb-5 flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                <XCircle size={18} />
                {configError}
              </div>
            )}


            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

              {/* Jira URL */}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Jira URL
                </label>

                <input
                  type="text"
                  value={jiraUrl}
                  onChange={(e) =>
                    setJiraUrl(e.target.value)
                  }
                  placeholder="https://yourcompany.atlassian.net"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>


              {/* Jira Email */}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Jira Email
                </label>

                <input
                  type="email"
                  value={jiraEmail}
                  onChange={(e) =>
                    setJiraEmail(e.target.value)
                  }
                  placeholder="jira-user@company.com"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>


              {/* API Token */}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Jira API Token
                </label>

                <input
                  type="password"
                  value={jiraApiToken}
                  onChange={(e) =>
                    setJiraApiToken(e.target.value)
                  }
                  placeholder={
                    hasApiToken
                      ? "Token already configured — leave blank to keep it"
                      : "Enter Jira API token"
                  }
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />

                {hasApiToken && (
                  <p className="text-xs text-green-600 mt-1">
                    API token is already configured.
                  </p>
                )}
              </div>


              {/* Active */}

              <div className="flex items-center">

                <label className="flex items-center gap-3 cursor-pointer">

                  <input
                    type="checkbox"
                    checked={active}
                    onChange={(e) =>
                      setActive(
                        e.target.checked
                      )
                    }
                    className="w-4 h-4 text-blue-600 rounded"
                  />

                  <span className="text-sm font-medium text-gray-700">
                    Jira integration active
                  </span>

                </label>

              </div>


              {/* Bug JQL */}

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Bug JQL
                </label>

                <textarea
                  value={jql}
                  onChange={(e) =>
                    setJql(e.target.value)
                  }
                  rows={3}
                  placeholder='project = ABC AND issuetype = Bug'
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                />

                <p className="text-xs text-gray-500 mt-1">
                  JQL used to fetch Bugs.
                </p>
              </div>

              {/* Feature / Story JQL */}

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Feature / Story JQL
                </label>

                <textarea
                  value={featureJql}
                  onChange={(e) =>
                    setFeatureJql(e.target.value)
                  }
                  rows={3}
                  placeholder='project = ABC AND issuetype in ("Feature", "Story")'
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                />

                <p className="text-xs text-gray-500 mt-1">
                  Complete JQL used to fetch Features and Stories.
                </p>
              </div>

              {/* UAT Label */}

              {/* UAT Labels */}
<div>
  <TagInput
    label="UAT Issue Labels"
    tags={uatLabels}
    setTags={setUatLabels}
    placeholder="Type a label and press Enter"
  />

  <p className="text-xs text-gray-500 mt-1">
    Jira issues containing ANY of these labels will appear under UAT.
  </p>
</div>

{/* Production Labels */}
<div>
  <TagInput
    label="Production Issue Labels"
    tags={prodLabels}
    setTags={setProdLabels}
    placeholder="Type a label and press Enter"
  />

  <p className="text-xs text-gray-500 mt-1">
    Jira issues containing ANY of these labels will appear under Production.
  </p>
</div>
            </div>


            {/* Buttons */}

            <div className="mt-6 flex flex-wrap gap-3">

              <button
                type="button"
                onClick={handleSaveConfig}
                disabled={savingConfig}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50"
              >
                {savingConfig ? (
                  <>
                    <RefreshCw
                      size={16}
                      className="animate-spin"
                    />
                    Saving...
                  </>
                ) : (
                  <>
                    <ShieldCheck size={16} />
                    Save Configuration
                  </>
                )}
              </button>


              <button
                type="button"
                onClick={handleTestConnection}
                disabled={
                  testingConnection ||
                  !configured
                }
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-lg text-sm font-semibold hover:bg-gray-50 disabled:opacity-50"
              >
                {testingConnection ? (
                  <>
                    <RefreshCw
                      size={16}
                      className="animate-spin"
                    />
                    Testing...
                  </>
                ) : (
                  <>
                    <CheckCircle size={16} />
                    Test Connection
                  </>
                )}
              </button>

            </div>

          </div>

        </div>


        {/* ====================================================
            Not Configured
        ===================================================== */}

        {!configured && (
          <div className="bg-white rounded-xl border border-yellow-200 shadow-sm p-10 text-center">

            <div className="mx-auto w-12 h-12 rounded-full bg-yellow-50 flex items-center justify-center mb-4">
              <Settings
                size={24}
                className="text-yellow-600"
              />
            </div>

            <h2 className="text-lg font-semibold text-gray-900">
              Jira is not configured
            </h2>

            <p className="text-sm text-gray-500 mt-2">
              Configure Jira above to load issues for this project.
            </p>

          </div>
        )}


        {/* ====================================================
            Jira Issues
        ===================================================== */}

        {configured && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">

            {/* Issues header */}

            <div className="px-6 py-5 border-b border-gray-200">

              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">

                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    Jira Issues
                  </h2>

                  <p className="text-sm text-gray-500 mt-1">
                    View Jira issues by environment.
                  </p>
                </div>


                {/* Search */}

                <form
                  onSubmit={handleSearch}
                  className="flex items-center gap-2"
                >

                  <div className="relative">

                    <Search
                      size={17}
                      className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                    />

                    <input
                      type="text"
                      value={search}
                      onChange={(e) =>
                        setSearch(
                          e.target.value
                        )
                      }
                      placeholder="Search Jira ID or keyword"
                      className="w-72 border border-gray-300 rounded-lg pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />

                  </div>

                  <button
                    type="submit"
                    disabled={loadingBugs}
                    className="px-4 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50"
                  >
                    Search
                  </button>

                  {search && (
                    <button
                      type="button"
                      onClick={handleClearSearch}
                      className="px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50"
                    >
                      Clear
                    </button>
                  )}

                </form>

              </div>

            </div>


            {/* =================================================
                Tabs
            ================================================== */}

            <div className="px-6 pt-4 border-b border-gray-200">

              <div className="flex gap-8">

                {/* All */}

                <button
                  type="button"
                  onClick={() =>
                    setActiveTab("all")
                  }
                  className={`pb-3 text-sm font-semibold border-b-2 transition ${
                    activeTab === "all"
                      ? "text-blue-600 border-blue-600"
                      : "text-gray-500 border-transparent hover:text-gray-700"
                  }`}
                >
                  All

                  <span
                    className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                      activeTab === "all"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {bugs.length}
                  </span>

                </button>


                {/* UAT */}

                <button
                  type="button"
                  onClick={() =>
                    setActiveTab("uat")
                  }
                  className={`pb-3 text-sm font-semibold border-b-2 transition ${
                    activeTab === "uat"
                      ? "text-blue-600 border-blue-600"
                      : "text-gray-500 border-transparent hover:text-gray-700"
                  }`}
                >
                  UAT

                  <span
                    className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                      activeTab === "uat"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {uatBugs.length}
                  </span>

                </button>


                {/* Production */}

                <button
                  type="button"
                  onClick={() =>
                    setActiveTab("prod")
                  }
                  className={`pb-3 text-sm font-semibold border-b-2 transition ${
                    activeTab === "prod"
                      ? "text-blue-600 border-blue-600"
                      : "text-gray-500 border-transparent hover:text-gray-700"
                  }`}
                >
                  Production

                  <span
                    className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                      activeTab === "prod"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {prodBugs.length}
                  </span>

                </button>

              </div>

            </div>


            {/* =================================================
                Search info
            ================================================== */}

            {search && (
              <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">

                <p className="text-sm text-gray-600">
                  Search results for{" "}
                  <span className="font-semibold text-gray-900">
                    "{search}"
                  </span>
                </p>

              </div>
            )}


            {/* =================================================
                Error
            ================================================== */}

            {bugsError && (
              <div className="mx-6 mt-5 flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                <XCircle size={18} />
                {bugsError}
              </div>
            )}


            {/* =================================================
                Loading
            ================================================== */}

            {loadingBugs && (
              <div className="py-12 flex items-center justify-center gap-3 text-gray-500">
                <RefreshCw
                  size={20}
                  className="animate-spin"
                />
                Loading Jira issues...
              </div>
            )}


            {/* =================================================
                Content
            ================================================== */}

            {!loadingBugs && !bugsError && (
              <>

                {/* Table title */}

                <div className="px-6 py-4 flex items-center justify-between">

                  <div>

                    <h3 className="font-semibold text-gray-900">

                      {activeTab === "all"
                        ? "All Jira Issues"
                        : activeTab === "uat"
                          ? "UAT Issues"
                          : "Production Issues"}

                    </h3>

                    <p className="text-xs text-gray-500 mt-1">
                      Showing{" "}
                      <span className="font-semibold">
                        {visibleBugs.length}
                      </span>{" "}
                      issues
                    </p>

                  </div>

                </div>


                {/* Empty state */}

                {visibleBugs.length === 0 ? (
                  <div className="px-6 py-14 text-center">

                    <div className="mx-auto w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-4">
                      <Search
                        size={22}
                        className="text-gray-400"
                      />
                    </div>

                    <h3 className="text-sm font-semibold text-gray-900">
                      No issues found
                    </h3>

                    <p className="text-sm text-gray-500 mt-1">
                      There are no Jira issues matching this view.
                    </p>

                  </div>
                ) : (

                  /* =================================================
                     Table
                  ================================================== */

                  <div className="overflow-x-auto">

                    <table className="w-full text-sm">

                      <thead className="bg-gray-50 border-y border-gray-200">

                        <tr>

                          <th className="text-left px-6 py-3 font-semibold text-gray-600 whitespace-nowrap">
                            Jira ID
                          </th>

                          <th className="text-left px-4 py-3 font-semibold text-gray-600 min-w-[300px]">
                            Summary
                          </th>

                          <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">
                            Status
                          </th>

                          <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">
                            Priority
                          </th>

                          <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">
                            Assignee
                          </th>

                          <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">
                            Reporter
                          </th>

                          <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">
                            Created
                          </th>

                          <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">
                            Updated
                          </th>

                          <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">
                            Environment
                          </th>

                        </tr>

                      </thead>


                      <tbody className="divide-y divide-gray-100">

                        {visibleBugs.map(
                          (bug) => (

                            <tr
                              key={
                                bug.jira_id
                              }
                              className="hover:bg-gray-50"
                            >

                              {/* Jira ID */}

                              <td className="px-6 py-4 whitespace-nowrap">

                                <a
                                  href={getJiraIssueUrl(
                                    bug.jira_id
                                  )}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex items-center gap-1 font-semibold text-blue-600 hover:text-blue-800"
                                >
                                  {bug.jira_id}

                                  <ExternalLink
                                    size={13}
                                  />
                                </a>

                              </td>


                              {/* Summary */}

                              <td className="px-4 py-4">

                                <div
                                  className="max-w-[420px] truncate text-gray-900"
                                  title={
                                    bug.summary ||
                                    ""
                                  }
                                >
                                  {bug.summary ||
                                    "-"}
                                </div>

                              </td>


                              {/* Status */}

                              <td className="px-4 py-4 whitespace-nowrap">

                                <span
                                  className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${getStatusClass(
                                    bug.status
                                  )}`}
                                >
                                  {bug.status ||
                                    "-"}
                                </span>

                              </td>


                              {/* Priority */}

                              <td className="px-4 py-4 whitespace-nowrap">

                                <span
                                  className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${getPriorityClass(
                                    bug.priority
                                  )}`}
                                >
                                  {bug.priority ||
                                    "-"}
                                </span>

                              </td>


                              {/* Assignee */}

                              <td className="px-4 py-4 whitespace-nowrap text-gray-700">
                                {bug.assignee ||
                                  "-"}
                              </td>


                              {/* Reporter */}

                              <td className="px-4 py-4 whitespace-nowrap text-gray-700">
                                {bug.reporter ||
                                  "-"}
                              </td>


                              {/* Created */}

                              <td className="px-4 py-4 whitespace-nowrap text-gray-600">
                                {formatDate(
                                  bug.created
                                )}
                              </td>


                              {/* Updated */}

                              <td className="px-4 py-4 whitespace-nowrap text-gray-600">
                                {formatDate(
                                  bug.updated
                                )}
                              </td>


                              {/* Environment */}

                              <td className="px-4 py-4 whitespace-nowrap">

                                {bug.environment ===
                                "UAT" ? (
                                  <span className="inline-flex px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-700">
                                    UAT
                                  </span>
                                ) : bug.environment ===
                                  "PROD" ? (
                                  <span className="inline-flex px-2.5 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-700">
                                    Production
                                  </span>
                                ) : (
                                  <span className="inline-flex px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                                    -
                                  </span>
                                )}

                              </td>

                            </tr>

                          )
                        )}

                      </tbody>

                    </table>

                  </div>

                )}

              </>
            )}

          </div>
        )}

      </div>

    </div>
  );
}


        {/* ====================================================
            Features / Stories
        ===================================================== */}

        {configured && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm mt-6">
            <div className="px-6 py-5 border-b border-gray-200">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Features & Stories</h2>
                  <p className="text-sm text-gray-500 mt-1">
                    View Features and Stories using the configured Feature / Story JQL.
                  </p>
                </div>

                <form onSubmit={handleFeatureSearch} className="flex items-center gap-2">
                  <div className="relative">
                    <Search size={17} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      value={featureSearch}
                      onChange={(e) => setFeatureSearch(e.target.value)}
                      placeholder="Search Feature / Story"
                      className="w-72 border border-gray-300 rounded-lg pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={loadingFeatures}
                    className="px-4 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50"
                  >Search</button>
                  {featureSearch && (
                    <button
                      type="button"
                      onClick={handleClearFeatureSearch}
                      className="px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50"
                    >Clear</button>
                  )}
                </form>
              </div>
            </div>

            {featureSearch && (
              <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
                <p className="text-sm text-gray-600">
                  Feature / Story search results for {""}
                  <span className="font-semibold text-gray-900">"{featureSearch}"</span>
                </p>
              </div>
            )}

            {featureError && (
              <div className="mx-6 mt-5 flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                <XCircle size={18} />
                {featureError}
              </div>
            )}

            {loadingFeatures && (
              <div className="py-12 flex items-center justify-center gap-3 text-gray-500">
                <RefreshCw size={20} className="animate-spin" />
                Loading Features and Stories...
              </div>
            )}

            {!loadingFeatures && !featureError && (
              <>
                <div className="px-6 py-4 flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">Feature / Story Issues</h3>
                    <p className="text-xs text-gray-500 mt-1">
                      Showing <span className="font-semibold">{features.length}</span> of {""}
                      <span className="font-semibold">{featureTotal}</span> issues
                    </p>
                  </div>
                </div>

                {features.length === 0 ? (
                  <div className="px-6 py-14 text-center">
                    <div className="mx-auto w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-4">
                      <Search size={22} className="text-gray-400" />
                    </div>
                    <h3 className="text-sm font-semibold text-gray-900">No Features or Stories found</h3>
                    <p className="text-sm text-gray-500 mt-1">
                      Check your Feature / Story JQL or try a different search.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 border-y border-gray-200">
                        <tr>
                          <th className="text-left px-6 py-3 font-semibold text-gray-600 whitespace-nowrap">Jira ID</th>
                          <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">Type</th>
                          <th className="text-left px-4 py-3 font-semibold text-gray-600 min-w-[300px]">Summary</th>
                          <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">Status</th>
                          <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">Priority</th>
                          <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">Assignee</th>
                          <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">Story Points</th>
                          <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">Created</th>
                          <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">Updated</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {features.map((issue) => (
                          <tr key={issue.jira_id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <a href={getJiraIssueUrl(issue.jira_id)} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 font-semibold text-blue-600 hover:text-blue-800">
                                {issue.jira_id}<ExternalLink size={13} />
                              </a>
                            </td>
                            <td className="px-4 py-4 whitespace-nowrap">
                              <span className="inline-flex px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-700">
                                {issue.issue_type || issue.type || "-"}
                              </span>
                            </td>
                            <td className="px-4 py-4">
                              <div className="max-w-[420px] truncate text-gray-900" title={issue.summary || ""}>{issue.summary || "-"}</div>
                            </td>
                            <td className="px-4 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${getStatusClass(issue.status)}`}>{issue.status || "-"}</span>
                            </td>
                            <td className="px-4 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${getPriorityClass(issue.priority)}`}>{issue.priority || "-"}</span>
                            </td>
                            <td className="px-4 py-4 whitespace-nowrap text-gray-700">{issue.assignee || "-"}</td>
                            <td className="px-4 py-4 whitespace-nowrap text-gray-700">{issue.story_points ?? "-"}</td>
                            <td className="px-4 py-4 whitespace-nowrap text-gray-600">{formatDate(issue.created)}</td>
                            <td className="px-4 py-4 whitespace-nowrap text-gray-600">{formatDate(issue.updated)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {featureTotal > 0 && featurePages > 1 && (
                  <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                    <p className="text-sm text-gray-500">
                      Page <span className="font-semibold text-gray-900">{featurePage}</span> of {""}
                      <span className="font-semibold text-gray-900">{featurePages}</span>
                    </p>
                    <div className="flex items-center gap-2">
                      <button type="button" onClick={() => setFeaturePage((page) => Math.max(1, page - 1))} disabled={featurePage === 1 || loadingFeatures} className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50">Previous</button>
                      <button type="button" onClick={() => setFeaturePage((page) => Math.min(featurePages, page + 1))} disabled={featurePage >= featurePages || loadingFeatures} className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50">Next</button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

export default JiraDetails;
