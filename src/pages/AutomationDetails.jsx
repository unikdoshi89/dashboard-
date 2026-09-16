import React, {
  useEffect,
  useState,
} from "react";

import {
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  Plus,
  Pencil,
  Trash2,
  ChevronDown,
  ChevronRight,
  Upload,
} from "lucide-react";

import {
  getAutomationDetails,
  createAutomationRelease,
  createAutomationPod,
  updateAutomationPod,
  deleteAutomationPod,
} from "../api/automation";

import {
  uploadAutomationExcel,
  getLatestAutomationUpload,
} from "../api/projects";

import AddReleaseModal from "../components/AddReleaseModal";
import AddAutomationPodModal from "../components/AddAutomationPodModal";
import EditAutomationPodModal from "../components/EditAutomationPodModal";


function AutomationDetails() {

  // ==================================================
  // Route
  // ==================================================

  const { projectId } = useParams();

  const routeProjectId = Number(projectId);

  const navigate = useNavigate();


  // ==================================================
  // State
  // ==================================================

  const [automation, setAutomation] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");


  // ==================================================
  // Release / POD State
  // ==================================================

  const [showAddRelease, setShowAddRelease] =
    useState(false);

  const [showAddPod, setShowAddPod] =
    useState(false);

  const [showEditPod, setShowEditPod] =
    useState(false);

  const [selectedRelease, setSelectedRelease] =
    useState(null);

  const [selectedDetail, setSelectedDetail] =
    useState(null);

  const [expandedReleases, setExpandedReleases] =
    useState({});


  // ==================================================
  // Excel Upload State
  // ==================================================

  const [selectedFile, setSelectedFile] =
    useState(null);

  const [uploading, setUploading] =
    useState(false);

  const [uploadMessage, setUploadMessage] =
    useState("");

  const [uploadMessageType, setUploadMessageType] =
    useState("");

  const [uploadedData, setUploadedData] =
    useState(null);


  // ==================================================
  // Load Automation
  // ==================================================

  async function loadAutomation() {

    if (!routeProjectId) {
      return;
    }

    try {

      setLoading(true);
      setError("");

      console.log(
        "Loading automation for project:",
        routeProjectId
      );

      const data =
        await getAutomationDetails(
          routeProjectId
        );

      setAutomation(data);


      // Expand all releases by default
      const expanded = {};

      (data.releases || []).forEach(
        (release) => {
          expanded[release.id] = true;
        }
      );

      setExpandedReleases(expanded);

    } catch (err) {

      console.error(
        "Failed to load automation:",
        err
      );

      setError(
        err?.response?.data?.detail ||
        "Failed to load automation details"
      );

    } finally {

      setLoading(false);

    }

  }


  // ==================================================
  // Load Latest Excel Upload
  // ==================================================

  async function loadLatestAutomationUpload() {

    if (!routeProjectId) {
      return;
    }

    try {

      const data =
        await getLatestAutomationUpload(
          routeProjectId
        );

      setUploadedData(data);

    } catch (err) {

      console.error(
        "Failed to load automation Excel:",
        err
      );

      setUploadedData(null);

    }

  }


  // ==================================================
  // Initial Load
  // ==================================================

  useEffect(() => {

    if (!routeProjectId) {
      return;
    }

    loadAutomation();
    loadLatestAutomationUpload();

  }, [routeProjectId]);


  // ==================================================
  // Excel File Selected
  // ==================================================

  function handleExcelFileSelected(event) {

    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }


    // Validate extension
    const fileName =
      file.name.toLowerCase();

    if (!fileName.endsWith(".xlsx")) {

      setSelectedFile(null);

      setUploadMessage(
        "Please select a valid .xlsx Excel file."
      );

      setUploadMessageType("error");

      return;

    }


    // Clear previous message
    setUploadMessage("");
    setUploadMessageType("");


    // Store selected file
    setSelectedFile(file);


    // Allow selecting same file again
    event.target.value = "";

  }


  // ==================================================
  // Upload Excel
  // ==================================================

  async function handleAutomationExcelUpload() {

    if (!routeProjectId) {

      setUploadMessage(
        "Invalid project."
      );

      setUploadMessageType("error");

      return;

    }


    if (!selectedFile) {

      setUploadMessage(
        "Please select an Excel file."
      );

      setUploadMessageType("error");

      return;

    }


    try {

      setUploading(true);

      setUploadMessage("");
      setUploadMessageType("");


      const result =
        await uploadAutomationExcel(
          routeProjectId,
          selectedFile
        );


      setUploadMessage(
        `${result.rows_imported} rows uploaded successfully.`
      );

      setUploadMessageType("success");


      // Clear selected file
      setSelectedFile(null);


      // Reload latest uploaded Excel
      await loadLatestAutomationUpload();


    } catch (err) {

      console.error(
        "Automation Excel upload failed:",
        err
      );


      const message =
        err?.response?.data?.detail ||
        "Excel upload failed.";


      setUploadMessage(
        typeof message === "string"
          ? message
          : "Invalid Excel format."
      );

      setUploadMessageType("error");

    } finally {

      setUploading(false);

    }

  }


  // ==================================================
  // Toggle Release
  // ==================================================

  function toggleRelease(
    releaseId
  ) {

    setExpandedReleases(
      (previous) => ({
        ...previous,
        [releaseId]:
          !previous[releaseId],
      })
    );

  }


  // ==================================================
  // Create Release
  // ==================================================

  async function handleCreateRelease(
    data
  ) {

    try {

      setError("");

      await createAutomationRelease(
        routeProjectId,
        data
      );

      setShowAddRelease(false);

      await loadAutomation();

    } catch (err) {

      console.error(
        "Failed to create release:",
        err
      );

      setError(
        err?.response?.data?.detail ||
        "Failed to create release"
      );

    }

  }


  // ==================================================
  // Add POD
  // ==================================================

  async function handleAddPod(
    data
  ) {

    if (!selectedRelease) {
      return;
    }

    try {

      setError("");

      await createAutomationPod(
        routeProjectId,
        selectedRelease.id,
        data
      );

      setShowAddPod(false);

      setSelectedRelease(null);

      await loadAutomation();

    } catch (err) {

      console.error(
        "Failed to add POD:",
        err
      );

      setError(
        err?.response?.data?.detail ||
        "Failed to add POD"
      );

    }

  }


  // ==================================================
  // Edit POD
  // ==================================================

  async function handleUpdatePod(
    data
  ) {

    if (!selectedDetail) {
      return;
    }

    try {

      setError("");

      await updateAutomationPod(
        selectedDetail.id,
        data
      );

      setShowEditPod(false);

      setSelectedDetail(null);

      await loadAutomation();

    } catch (err) {

      console.error(
        "Failed to update POD:",
        err
      );

      setError(
        err?.response?.data?.detail ||
        "Failed to update POD"
      );

    }

  }


  // ==================================================
  // Delete POD
  // ==================================================

  async function handleDeletePod(
    detail
  ) {

    const confirmed =
      window.confirm(
        `Delete ${detail.pod}?`
      );

    if (!confirmed) {
      return;
    }


    try {

      setError("");

      await deleteAutomationPod(
        detail.id
      );

      await loadAutomation();

    } catch (err) {

      console.error(
        "Failed to delete POD:",
        err
      );

      setError(
        err?.response?.data?.detail ||
        "Failed to delete POD"
      );

    }

  }


  // ==================================================
  // Render
  // ==================================================

  return (

    <div
      className="
        min-h-screen
        bg-gray-50
      "
    >

      {/* ==================================================
          Page Header
          ================================================== */}

      <header
        className="
          bg-white
          border-b
          border-gray-200
        "
      >

        <div
          className="
            max-w-7xl
            mx-auto
            px-6
            py-4
            flex
            items-center
            justify-between
          "
        >

          <div>

            <h1
              className="
                text-xl
                font-bold
                text-gray-900
              "
            >
              Automation Details
            </h1>

            <p
              className="
                text-sm
                text-gray-500
              "
            >
              Release automation coverage and stability
            </p>

          </div>


          <button
            type="button"
            onClick={() => navigate("/")}
            className="
              inline-flex
              items-center
              gap-2
              px-4
              py-2.5
              bg-white
              border
              border-gray-200
              rounded-lg
              text-sm
              font-medium
              text-gray-700
              hover:bg-gray-50
            "
          >
            ← Back to Dashboard
          </button>

        </div>

      </header>


      {/* ==================================================
          Main
          ================================================== */}

      <main
        className="
          max-w-7xl
          mx-auto
          px-6
          py-8
        "
      >

        {/* ==================================================
            Error
            ================================================== */}

        {error && (

          <div
            className="
              mb-6
              p-4
              bg-red-50
              border
              border-red-200
              text-red-700
              rounded-lg
            "
          >
            {error}
          </div>

        )}


        {/* ==================================================
            Loading
            ================================================== */}

        {loading && (

          <div
            className="
              text-center
              py-10
              text-gray-500
            "
          >
            Loading automation details...
          </div>

        )}


        {/* ==================================================
            Automation Content
            ================================================== */}

        {!loading && automation && (

          <>

            {/* ==================================================
                Summary Cards
                ================================================== */}

            <div
              className="
                grid
                grid-cols-1
                sm:grid-cols-2
                lg:grid-cols-5
                gap-4
                mb-8
              "
            >

              <SummaryCard
                title="Releases"
                value={
                  automation.releases?.length || 0
                }
              />


              <SummaryCard
                title="Requirements + RTB"
                value={
                  automation.totals
                    ?.requirements_rtb ?? 0
                }
              />


              <SummaryCard
                title="Test Cases"
                value={
                  automation.totals
                    ?.test_cases ?? 0
                }
              />


              <SummaryCard
                title="Automatable"
                value={
                  automation.totals
                    ?.automatable ?? 0
                }
              />


              <SummaryCard
                title="Automation Coverage"
                value={
                  automation.totals
                    ?.automation_percentage !== null &&
                  automation.totals
                    ?.automation_percentage !== undefined
                    ? `${automation.totals.automation_percentage}%`
                    : "—"
                }
              />

            </div>


            {/* ==================================================
                Main Automation Card
                ================================================== */}

            <div
              className="
                bg-white
                border
                border-gray-200
                rounded-xl
                shadow-sm
                overflow-hidden
              "
            >

              {/* ==================================================
                  Section Header
                  ================================================== */}

              <div
                className="
                  px-6
                  py-5
                  border-b
                  border-gray-200
                  flex
                  items-center
                  justify-between
                  gap-4
                "
              >

                <div>

                  <h2
                    className="
                      text-lg
                      font-semibold
                      text-gray-900
                    "
                  >
                    Release-wise Automation
                  </h2>

                  <p
                    className="
                      text-sm
                      text-gray-500
                      mt-1
                    "
                  >
                    Track test cases and automation coverage by POD
                  </p>

                </div>


                {/* ==================================================
                    Header Actions
                    ================================================== */}

                <div
                  className="
                    flex
                    items-center
                    gap-3
                    flex-shrink-0
                  "
                >

                  {/* Add Release */}

                  <button
                    type="button"
                    onClick={() =>
                      setShowAddRelease(true)
                    }
                    className="
                      inline-flex
                      items-center
                      gap-2
                      px-4
                      py-2.5
                      bg-blue-600
                      text-white
                      rounded-lg
                      text-sm
                      font-medium
                      hover:bg-blue-700
                    "
                  >

                    <Plus size={16} />

                    Add Release

                  </button>


                  {/* Upload Excel */}

                  <button
                    type="button"
                    onClick={() => {

                      document
                        .getElementById(
                          "automation-excel-upload"
                        )
                        ?.click();

                    }}
                    disabled={uploading}
                    className="
                      inline-flex
                      items-center
                      gap-2
                      px-4
                      py-2.5
                      bg-blue-600
                      text-white
                      rounded-lg
                      text-sm
                      font-medium
                      hover:bg-blue-700
                      disabled:opacity-50
                      disabled:cursor-not-allowed
                    "
                  >

                    <Upload size={16} />

                    Upload Excel

                  </button>


                  {/* Hidden File Input */}

                  <input
                    id="automation-excel-upload"
                    type="file"
                    accept=".xlsx"
                    className="hidden"
                    onChange={
                      handleExcelFileSelected
                    }
                  />

                </div>

              </div>


              {/* ==================================================
                  Selected Excel File
                  ================================================== */}

              {(selectedFile || uploadMessage) && (

                <div
                  className="
                    px-6
                    py-3
                    bg-gray-50
                    border-b
                    border-gray-200
                    flex
                    items-center
                    justify-between
                    gap-4
                  "
                >

                  <div
                    className="
                      flex
                      items-center
                      gap-3
                      min-w-0
                    "
                  >

                    {selectedFile && (

                      <div
                        className="
                          text-sm
                          text-gray-600
                          truncate
                        "
                      >

                        <span
                          className="
                            font-medium
                            text-gray-800
                          "
                        >
                          Selected file:
                        </span>{" "}

                        {selectedFile.name}

                      </div>

                    )}


                    {uploadMessage && (

                      <div
                        className={`
                          text-sm
                          ${
                            uploadMessageType === "error"
                              ? "text-red-600"
                              : "text-green-600"
                          }
                        `}
                      >
                        {uploadMessage}
                      </div>

                    )}

                  </div>


                  {selectedFile && (

                    <button
                      type="button"
                      onClick={
                        handleAutomationExcelUpload
                      }
                      disabled={uploading}
                      className="
                        inline-flex
                        items-center
                        gap-2
                        px-3
                        py-2
                        bg-green-600
                        text-white
                        rounded-lg
                        text-sm
                        font-medium
                        hover:bg-green-700
                        disabled:opacity-50
                        disabled:cursor-not-allowed
                        flex-shrink-0
                      "
                    >

                      <Upload size={15} />

                      {uploading
                        ? "Uploading..."
                        : "Upload Selected File"}

                    </button>

                  )}

                </div>

              )}


              {/* ==================================================
                  Latest Uploaded Excel
                  ================================================== */}

              {uploadedData?.upload && (

                <div
                  className="
                    border-b
                    border-gray-200
                  "
                >

                  {/* Upload Information */}

                  <div
                    className="
                      px-6
                      py-4
                      bg-blue-50
                      border-b
                      border-blue-100
                    "
                  >

                    <div
                      className="
                        flex
                        items-center
                        justify-between
                        gap-4
                      "
                    >

                      <div>

                        <h3
                          className="
                            text-sm
                            font-semibold
                            text-gray-900
                          "
                        >
                          Latest Automation Upload
                        </h3>

                        <div
                          className="
                            flex
                            flex-wrap
                            items-center
                            gap-x-6
                            gap-y-1
                            mt-2
                            text-xs
                            text-gray-600
                          "
                        >

                          <span>

                            <strong>
                              File:
                            </strong>{" "}

                            {uploadedData.upload.filename}

                          </span>


                          <span>

                            <strong>
                              Records:
                            </strong>{" "}

                            {uploadedData.upload.row_count}

                          </span>


                          <span>

                            <strong>
                              Uploaded:
                            </strong>{" "}

                            {new Date(
                              uploadedData
                                .upload
                                .uploaded_at
                            ).toLocaleString()}

                          </span>

                        </div>

                      </div>

                    </div>

                  </div>


                  {/* Uploaded Excel Table */}

                  <div
                    className="
                      overflow-x-auto
                    "
                  >

                    <table
                      className="
                        w-full
                        text-sm
                        min-w-[1000px]
                      "
                    >

                      <thead>

                        <tr
                          className="
                            bg-gray-50
                            border-b
                            border-gray-200
                          "
                        >

                          <th
                            className="
                              px-5
                              py-3
                              text-left
                              font-semibold
                              text-gray-700
                              whitespace-nowrap
                            "
                          >
                            S. No.
                          </th>


                          <th
                            className="
                              px-5
                              py-3
                              text-left
                              font-semibold
                              text-gray-700
                              whitespace-nowrap
                            "
                          >
                            Jira ID
                          </th>


                          <th
                            className="
                              px-5
                              py-3
                              text-left
                              font-semibold
                              text-gray-700
                              whitespace-nowrap
                            "
                          >
                            Test Case ID
                          </th>


                          <th
                            className="
                              px-5
                              py-3
                              text-left
                              font-semibold
                              text-gray-700
                              whitespace-nowrap
                            "
                          >
                            Owner
                          </th>


                          <th
                            className="
                              px-5
                              py-3
                              text-left
                              font-semibold
                              text-gray-700
                              min-w-[300px]
                            "
                          >
                            Test Case Description
                          </th>


                          <th
                            className="
                              px-5
                              py-3
                              text-left
                              font-semibold
                              text-gray-700
                              whitespace-nowrap
                            "
                          >
                            Status
                          </th>


                          <th
                            className="
                              px-5
                              py-3
                              text-center
                              font-semibold
                              text-gray-700
                              whitespace-nowrap
                            "
                          >
                            Automat-able
                          </th>


                          <th
                            className="
                              px-5
                              py-3
                              text-center
                              font-semibold
                              text-gray-700
                              whitespace-nowrap
                            "
                          >
                            Automated
                          </th>

                        </tr>

                      </thead>


                      <tbody>

                        {(uploadedData.rows || [])
                          .map((row) => (

                            <tr
                              key={row.id}
                              className="
                                border-b
                                border-gray-100
                                hover:bg-gray-50
                              "
                            >

                              <td
                                className="
                                  px-5
                                  py-3
                                  text-gray-700
                                "
                              >
                                {row.sno ?? "-"}
                              </td>


                              <td
                                className="
                                  px-5
                                  py-3
                                  text-gray-700
                                "
                              >
                                {row.jira_id || "-"}
                              </td>


                              <td
                                className="
                                  px-5
                                  py-3
                                  font-medium
                                  text-gray-900
                                "
                              >
                                {row.test_case_id}
                              </td>


                              <td
                                className="
                                  px-5
                                  py-3
                                  text-gray-700
                                "
                              >
                                {row.owner || "-"}
                              </td>


                              <td
                                className="
                                  px-5
                                  py-3
                                  text-gray-700
                                  max-w-[450px]
                                "
                              >
                                <div
                                  className="
                                    truncate
                                  "
                                  title={
                                    row.test_case_description ||
                                    ""
                                  }
                                >
                                  {
                                    row.test_case_description ||
                                    "-"
                                  }
                                </div>
                              </td>


                              <td
                                className="
                                  px-5
                                  py-3
                                  text-gray-700
                                "
                              >
                                {row.status || "-"}
                              </td>


                              <td
                                className="
                                  px-5
                                  py-3
                                  text-center
                                  font-medium
                                "
                              >
                                {row.automatable || "-"}
                              </td>


                              <td
                                className="
                                  px-5
                                  py-3
                                  text-center
                                  font-medium
                                "
                              >
                                {row.automated || "-"}
                              </td>

                            </tr>

                          ))}


                        {(!uploadedData.rows ||
                          uploadedData.rows.length === 0) && (

                          <tr>

                            <td
                              colSpan="8"
                              className="
                                px-6
                                py-8
                                text-center
                                text-gray-500
                              "
                            >
                              No records found in the latest Excel upload.
                            </td>

                          </tr>

                        )}

                      </tbody>

                    </table>

                  </div>

                </div>

              )}


              {/* ==================================================
                  Release Automation Table
                  ================================================== */}

              <div
                className="
                  overflow-x-auto
                "
              >

                <table
                  className="
                    w-full
                    min-w-[900px]
                    text-sm
                  "
                >

                  {/* ==================================================
                      Table Header
                      ================================================== */}

                  <thead>

                    <tr
                      className="
                        bg-gray-50
                        border-b
                        border-gray-200
                      "
                    >

                      <th
                        className="
                          px-5
                          py-3
                          text-left
                          font-semibold
                          text-gray-700
                        "
                      >
                        #
                      </th>


                      <th
                        className="
                          px-5
                          py-3
                          text-left
                          font-semibold
                          text-gray-700
                        "
                      >
                        POD
                      </th>


                      <th
                        className="
                          px-5
                          py-3
                          text-right
                          font-semibold
                          text-gray-700
                        "
                      >
                        Requirements + RTB
                      </th>


                      <th
                        className="
                          px-5
                          py-3
                          text-right
                          font-semibold
                          text-gray-700
                        "
                      >
                        Test Cases
                      </th>


                      <th
                        className="
                          px-5
                          py-3
                          text-right
                          font-semibold
                          text-gray-700
                        "
                      >
                        Automatable
                      </th>


                      <th
                        className="
                          px-5
                          py-3
                          text-right
                          font-semibold
                          text-gray-700
                        "
                      >
                        Automated
                      </th>


                      <th
                        className="
                          px-5
                          py-3
                          text-right
                          font-semibold
                          text-gray-700
                        "
                      >
                        Automation %
                      </th>


                      <th
                        className="
                          px-5
                          py-3
                          text-center
                          font-semibold
                          text-gray-700
                        "
                      >
                        Actions
                      </th>

                    </tr>

                  </thead>


                  {/* ==================================================
                      Table Body
                      ================================================== */}

                  <tbody>

                    {/* No Release */}

                    {(!automation.releases ||
                      automation.releases.length === 0) && (

                      <tr>

                        <td
                          colSpan="8"
                          className="
                            px-6
                            py-12
                            text-center
                            text-gray-500
                          "
                        >
                          No automation data available.
                        </td>

                      </tr>

                    )}


                    {/* Releases */}

                    {(automation.releases || [])
                      .map((release) => {

                        const expanded =
                          expandedReleases[
                            release.id
                          ];


                        return (

                          <React.Fragment
                            key={release.id}
                          >

                            {/* Release Row */}

                            <tr
                              className="
                                bg-blue-50
                                border-b
                                border-blue-100
                              "
                            >

                              <td
                                colSpan="8"
                                className="
                                  px-5
                                  py-3
                                "
                              >

                                <div
                                  className="
                                    flex
                                    items-center
                                    justify-between
                                  "
                                >

                                  {/* Release Toggle */}

                                  <button
                                    type="button"
                                    onClick={() =>
                                      toggleRelease(
                                        release.id
                                      )
                                    }
                                    className="
                                      flex
                                      items-center
                                      gap-2
                                      font-semibold
                                      text-blue-900
                                    "
                                  >

                                    {expanded
                                      ? (
                                        <ChevronDown
                                          size={18}
                                        />
                                      )
                                      : (
                                        <ChevronRight
                                          size={18}
                                        />
                                      )
                                    }

                                    {
                                      release.release_name
                                    }

                                  </button>


                                  {/* Add POD */}

                                  <button
                                    type="button"
                                    onClick={() => {

                                      setSelectedRelease(
                                        release
                                      );

                                      setShowAddPod(
                                        true
                                      );

                                    }}
                                    className="
                                      inline-flex
                                      items-center
                                      gap-1
                                      text-sm
                                      text-blue-700
                                      font-medium
                                      hover:text-blue-900
                                    "
                                  >

                                    <Plus
                                      size={15}
                                    />

                                    Add POD

                                  </button>

                                </div>

                              </td>

                            </tr>


                            {/* POD Rows */}

                            {expanded &&
                              (release.pods || [])
                                .map((detail) => (

                                  <tr
                                    key={detail.id}
                                    className="
                                      border-b
                                      border-gray-100
                                      hover:bg-gray-50
                                    "
                                  >

                                    {/* Indentation */}

                                    <td
                                      className="
                                        px-5
                                        py-3
                                      "
                                    />


                                    {/* POD */}

                                    <td
                                      className="
                                        px-5
                                        py-3
                                        font-medium
                                        text-gray-900
                                      "
                                    >
                                      {detail.pod}
                                    </td>


                                    {/* Requirements */}

                                    <td
                                      className="
                                        px-5
                                        py-3
                                        text-right
                                        text-gray-700
                                      "
                                    >
                                      {
                                        detail
                                          .requirements_rtb
                                      }
                                    </td>


                                    {/* Test Cases */}

                                    <td
                                      className="
                                        px-5
                                        py-3
                                        text-right
                                        text-gray-700
                                      "
                                    >
                                      {
                                        detail
                                          .test_cases
                                      }
                                    </td>


                                    {/* Automatable */}

                                    <td
                                      className="
                                        px-5
                                        py-3
                                        text-right
                                        text-gray-700
                                      "
                                    >
                                      {
                                        detail
                                          .automatable
                                      }
                                    </td>


                                    {/* Automated */}

                                    <td
                                      className="
                                        px-5
                                        py-3
                                        text-right
                                        text-gray-700
                                      "
                                    >
                                      {
                                        detail
                                          .automated
                                      }
                                    </td>


                                    {/* Automation % */}

                                    <td
                                      className="
                                        px-5
                                        py-3
                                        text-right
                                        font-medium
                                        text-gray-900
                                      "
                                    >

                                      {
                                        detail
                                          .automation_percentage !==
                                          null &&
                                        detail
                                          .automation_percentage !==
                                          undefined
                                          ? `${detail.automation_percentage}%`
                                          : "—"
                                      }

                                    </td>


                                    {/* Actions */}

                                    <td
                                      className="
                                        px-5
                                        py-3
                                      "
                                    >

                                      <div
                                        className="
                                          flex
                                          justify-center
                                          gap-2
                                        "
                                      >

                                        {/* Edit */}

                                        <button
                                          type="button"
                                          onClick={() => {

                                            setSelectedDetail(
                                              detail
                                            );

                                            setShowEditPod(
                                              true
                                            );

                                          }}
                                          className="
                                            p-2
                                            text-blue-600
                                            hover:bg-blue-50
                                            rounded-lg
                                          "
                                          title="Edit POD"
                                        >
                                          <Pencil
                                            size={16}
                                          />
                                        </button>


                                        {/* Delete */}

                                        <button
                                          type="button"
                                          onClick={() =>
                                            handleDeletePod(
                                              detail
                                            )
                                          }
                                          className="
                                            p-2
                                            text-red-600
                                            hover:bg-red-50
                                            rounded-lg
                                          "
                                          title="Delete POD"
                                        >
                                          <Trash2
                                            size={16}
                                          />
                                        </button>

                                      </div>

                                    </td>

                                  </tr>

                                ))
                            }

                          </React.Fragment>

                        );

                      })
                    }

                  </tbody>


                  {/* ==================================================
                      Total
                      ================================================== */}

                  <tfoot>

                    <tr
                      className="
                        bg-gray-100
                        border-t-2
                        border-gray-300
                        font-bold
                      "
                    >

                      <td
                        colSpan="2"
                        className="
                          px-5
                          py-4
                          text-gray-900
                        "
                      >
                        TOTAL
                      </td>


                      <td
                        className="
                          px-5
                          py-4
                          text-right
                        "
                      >
                        {
                          automation.totals
                            ?.requirements_rtb ?? 0
                        }
                      </td>


                      <td
                        className="
                          px-5
                          py-4
                          text-right
                        "
                      >
                        {
                          automation.totals
                            ?.test_cases ?? 0
                        }
                      </td>


                      <td
                        className="
                          px-5
                          py-4
                          text-right
                        "
                      >
                        {
                          automation.totals
                            ?.automatable ?? 0
                        }
                      </td>


                      <td
                        className="
                          px-5
                          py-4
                          text-right
                        "
                      >
                        {
                          automation.totals
                            ?.automated ?? 0
                        }
                      </td>


                      <td
                        className="
                          px-5
                          py-4
                          text-right
                        "
                      >

                        {
                          automation.totals
                            ?.automation_percentage !==
                            null &&
                          automation.totals
                            ?.automation_percentage !==
                            undefined
                            ? `${automation.totals.automation_percentage}%`
                            : "—"
                        }

                      </td>


                      <td />

                    </tr>

                  </tfoot>

                </table>

              </div>

            </div>

          </>

        )}

      </main>


      {/* ==================================================
          Add Release Modal
          ================================================== */}

      <AddReleaseModal
        open={showAddRelease}
        onClose={() =>
          setShowAddRelease(false)
        }
        onSave={
          handleCreateRelease
        }
      />


      {/* ==================================================
          Add POD Modal
          ================================================== */}

      <AddAutomationPodModal
        open={showAddPod}
        release={selectedRelease}
        onClose={() => {

          setShowAddPod(false);
          setSelectedRelease(null);

        }}
        onSave={
          handleAddPod
        }
      />


      {/* ==================================================
          Edit POD Modal
          ================================================== */}

      <EditAutomationPodModal
        open={showEditPod}
        detail={selectedDetail}
        onClose={() => {

          setShowEditPod(false);
          setSelectedDetail(null);

        }}
        onSave={
          handleUpdatePod
        }
      />

    </div>

  );

}


// ==================================================
// Summary Card
// ==================================================

function SummaryCard({
  title,
  value,
}) {

  return (

    <div
      className="
        bg-white
        border
        border-gray-200
        rounded-xl
        p-5
        shadow-sm
      "
    >

      <p
        className="
          text-sm
          text-gray-500
        "
      >
        {title}
      </p>


      <p
        className="
          text-2xl
          font-bold
          text-gray-900
          mt-2
        "
      >
        {value}
      </p>

    </div>

  );

}


export default AutomationDetails;
