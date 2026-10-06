import {
  useEffect,
  useState,
} from "react";

import {
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  ArrowLeft,
  Camera,
  RefreshCw,
  TrendingUp,
  Bug,
  Layers,
  ClipboardCheck,
  Bot,
  Activity,
} from "lucide-react";

import {
  getQETrends,
  createQESnapshot,
} from "../api/projects";

import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";


function QETrends() {

  const {
    projectId,
  } = useParams();

  const navigate =
    useNavigate();

  const [
    trendsData,
    setTrendsData,
  ] = useState(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    snapshotLoading,
    setSnapshotLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  const [
    months,
    setMonths,
  ] = useState(6);


  // ============================================================
  // Load Trends
  // ============================================================

  async function loadTrends() {

    if (!projectId) {
      return;
    }

    try {

      setLoading(true);
      setError("");

      const data =
        await getQETrends(
          projectId,
          months
        );

      setTrendsData(data);

    } catch (err) {

      console.error(
        "Failed to load QE trends:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Failed to load QE trends"
      );

    } finally {

      setLoading(false);

    }
  }


  useEffect(() => {

    loadTrends();

  }, [
    projectId,
    months,
  ]);


  // ============================================================
  // Capture Current Month
  // ============================================================

  async function handleCreateSnapshot() {

    if (!projectId) {
      return;
    }

    try {

      setSnapshotLoading(true);
      setError("");

      await createQESnapshot(
        projectId
      );

      await loadTrends();

    } catch (err) {

      console.error(
        "Failed to create QE snapshot:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Failed to create QE snapshot"
      );

    } finally {

      setSnapshotLoading(false);

    }
  }


  // ============================================================
  // Helpers
  // ============================================================

  function formatMonth(
    value
  ) {

    if (!value) {
      return "-";
    }

    const date =
      new Date(
        `${value}T00:00:00`
      );

    return date.toLocaleDateString(
      "en-US",
      {
        month: "short",
        year: "numeric",
      }
    );
  }


  function formatNumber(
    value
  ) {

    return Number(
      value || 0
    ).toLocaleString();
  }


  const trends =
    trendsData?.trends || [];

  const latest =
    trends.length > 0
      ? trends[
          trends.length - 1
        ]
      : null;

  const chartData =
    trends.map(
      (item) => ({
        ...item,

        month:
          formatMonth(
            item.snapshot_month
          ),
      })
    );


  // ============================================================
  // Loading
  // ============================================================

  if (
    loading &&
    !trendsData
  ) {

    return (
      <div className="min-h-screen bg-gray-50">

        <header className="bg-white border-b border-gray-200">

          <div className="max-w-7xl mx-auto px-6 py-4">

            <h1 className="text-xl font-bold text-gray-900">
              QE Trends
            </h1>

          </div>

        </header>

        <main className="max-w-7xl mx-auto px-6 py-16">

          <div className="text-center text-gray-500">

            Loading QE trends...

          </div>

        </main>

      </div>
    );
  }


  return (
    <div className="min-h-screen bg-gray-50">

      {/* ======================================================
          HEADER
          ====================================================== */}

      <header className="bg-white border-b border-gray-200">

        <div className="max-w-7xl mx-auto px-6 py-4">

          <div className="flex items-center justify-between gap-6">

            <div className="flex items-center gap-4">

              <button
                type="button"
                onClick={() =>
                  navigate(
                    `/?project=${projectId}`
                  )
                }
                className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50"
              >

                <ArrowLeft
                  size={16}
                />

                Dashboard

              </button>

              <div>

                <h1 className="text-xl font-bold text-gray-900">
                  QE Trends
                </h1>

                <p className="text-sm text-gray-500 mt-1">

                  {trendsData?.project_name ||
                    "Project"}

                </p>

              </div>

            </div>


            <div className="flex items-center gap-3">

              {/* Months */}

              <select
                value={months}
                onChange={(event) =>
                  setMonths(
                    Number(
                      event.target.value
                    )
                  )
                }
                className="px-3 py-2.5 border border-gray-300 rounded-lg text-sm bg-white"
              >

                <option value={3}>
                  Last 3 months
                </option>

                <option value={6}>
                  Last 6 months
                </option>

                <option value={12}>
                  Last 12 months
                </option>

                <option value={24}>
                  Last 24 months
                </option>

              </select>


              {/* Refresh */}

              <button
                type="button"
                onClick={loadTrends}
                disabled={loading}
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
              >

                <RefreshCw
                  size={16}
                  className={
                    loading
                      ? "animate-spin"
                      : ""
                  }
                />

                Refresh

              </button>


              {/* Snapshot */}

              <button
                type="button"
                onClick={
                  handleCreateSnapshot
                }
                disabled={
                  snapshotLoading
                }
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50"
              >

                <Camera
                  size={16}
                />

                {snapshotLoading
                  ? "Capturing..."
                  : "Capture Current Month"}

              </button>

            </div>

          </div>

        </div>

      </header>


      {/* ======================================================
          MAIN
          ====================================================== */}

      <main className="max-w-7xl mx-auto px-6 py-8">

        {/* Error */}

        {error && (

          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">

            {error}

          </div>

        )}


        {/* ====================================================
            EMPTY STATE
            ==================================================== */}

        {!latest && !loading && (

          <div className="bg-white border border-gray-200 rounded-xl p-12 text-center shadow-sm">

            <Activity
              size={42}
              className="mx-auto text-gray-400 mb-4"
            />

            <h2 className="text-lg font-semibold text-gray-900">

              No QE snapshots available

            </h2>

            <p className="text-sm text-gray-500 mt-2 mb-6">

              Capture the current month to
              start tracking QE trends.

            </p>

            <button
              type="button"
              onClick={
                handleCreateSnapshot
              }
              disabled={
                snapshotLoading
              }
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700"
            >

              <Camera
                size={16}
              />

              Capture Current Month

            </button>

          </div>

        )}


        {latest && (

          <>

            {/* ==================================================
                TITLE
                ================================================== */}

            <div className="mb-8">

              <h2 className="text-2xl font-bold text-gray-900">

                QE Performance Trends

              </h2>

              <p className="text-sm text-gray-500 mt-1">

                Historical quality engineering
                performance for{" "}

                <strong>
                  {trendsData.project_name}
                </strong>

              </p>

            </div>


            {/* ==================================================
                KPI CARDS
                ================================================== */}

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-5 mb-8">


              {/* Bugs */}

              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">

                <div className="flex items-center justify-between">

                  <div>

                    <p className="text-sm text-gray-500">
                      Total Bugs
                    </p>

                    <p className="text-2xl font-bold text-gray-900 mt-2">

                      {formatNumber(
                        latest.total_bugs
                      )}

                    </p>

                  </div>

                  <div className="p-3 bg-red-50 rounded-lg">

                    <Bug
                      size={22}
                      className="text-red-600"
                    />

                  </div>

                </div>

              </div>


              {/* Production */}

              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">

                <div className="flex items-center justify-between">

                  <div>

                    <p className="text-sm text-gray-500">
                      PROD Bugs
                    </p>

                    <p className="text-2xl font-bold text-gray-900 mt-2">

                      {formatNumber(
                        latest.prod_bugs
                      )}

                    </p>

                  </div>

                  <div className="p-3 bg-orange-50 rounded-lg">

                    <TrendingUp
                      size={22}
                      className="text-orange-600"
                    />

                  </div>

                </div>

              </div>


              {/* Features */}

              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">

                <div className="flex items-center justify-between">

                  <div>

                    <p className="text-sm text-gray-500">
                      Features
                    </p>

                    <p className="text-2xl font-bold text-gray-900 mt-2">

                      {formatNumber(
                        latest.total_features
                      )}

                    </p>

                  </div>

                  <div className="p-3 bg-blue-50 rounded-lg">

                    <Layers
                      size={22}
                      className="text-blue-600"
                    />

                  </div>

                </div>

              </div>


              {/* Test Cases */}

              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">

                <div className="flex items-center justify-between">

                  <div>

                    <p className="text-sm text-gray-500">
                      Test Cases
                    </p>

                    <p className="text-2xl font-bold text-gray-900 mt-2">

                      {formatNumber(
                        latest.total_test_cases
                      )}

                    </p>

                  </div>

                  <div className="p-3 bg-purple-50 rounded-lg">

                    <ClipboardCheck
                      size={22}
                      className="text-purple-600"
                    />

                  </div>

                </div>

              </div>


              {/* Coverage */}

              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">

                <div className="flex items-center justify-between">

                  <div>

                    <p className="text-sm text-gray-500">
                      Automation Coverage
                    </p>

                    <p className="text-2xl font-bold text-gray-900 mt-2">

                      {Number(
                        latest.automation_coverage ||
                        0
                      ).toFixed(2)}
                      %

                    </p>

                  </div>

                  <div className="p-3 bg-green-50 rounded-lg">

                    <Bot
                      size={22}
                      className="text-green-600"
                    />

                  </div>

                </div>

              </div>

            </div>


            {/* ==================================================
                BUG TREND
                ================================================== */}

            <section className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm mb-8">

              <div className="mb-6">

                <h3 className="text-lg font-semibold text-gray-900">

                  Bug Trend

                </h3>

                <p className="text-sm text-gray-500 mt-1">

                  Monthly total, SIT, UAT and
                  production bugs

                </p>

              </div>


              <div className="h-80">

                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >

                  <LineChart
                    data={chartData}
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="month"
                    />

                    <YAxis />

                    <Tooltip />

                    <Legend />

                    <Line
                      type="monotone"
                      dataKey="total_bugs"
                      name="Total Bugs"
                      stroke="#2563eb"
                      strokeWidth={3}
                    />

                    <Line
                      type="monotone"
                      dataKey="sit_bugs"
                      name="SIT"
                      stroke="#64748b"
                      strokeWidth={2}
                    />

                    <Line
                      type="monotone"
                      dataKey="uat_bugs"
                      name="UAT"
                      stroke="#f59e0b"
                      strokeWidth={2}
                    />

                    <Line
                      type="monotone"
                      dataKey="prod_bugs"
                      name="PROD"
                      stroke="#dc2626"
                      strokeWidth={2}
                    />

                  </LineChart>

                </ResponsiveContainer>

              </div>

            </section>


            {/* ==================================================
                TEST AUTOMATION TREND
                ================================================== */}

            <section className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm mb-8">

              <div className="mb-6">

                <h3 className="text-lg font-semibold text-gray-900">

                  Test Automation Trend

                </h3>

                <p className="text-sm text-gray-500 mt-1">

                  Test case growth and automation
                  progress

                </p>

              </div>


              <div className="h-80">

                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >

                  <BarChart
                    data={chartData}
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="month"
                    />

                    <YAxis />

                    <Tooltip />

                    <Legend />

                    <Bar
                      dataKey="total_test_cases"
                      name="Total Test Cases"
                      fill="#2563eb"
                    />

                    <Bar
                      dataKey="automatable_test_cases"
                      name="Automatable"
                      fill="#f59e0b"
                    />

                    <Bar
                      dataKey="automated_test_cases"
                      name="Automated"
                      fill="#16a34a"
                    />

                  </BarChart>

                </ResponsiveContainer>

              </div>

            </section>


            {/* ==================================================
                AUTOMATION COVERAGE
                ================================================== */}

            <section className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm mb-8">

              <div className="mb-6">

                <h3 className="text-lg font-semibold text-gray-900">

                  Automation Coverage

                </h3>

                <p className="text-sm text-gray-500 mt-1">

                  Percentage of automatable test
                  cases that are automated

                </p>

              </div>


              <div className="h-72">

                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >

                  <LineChart
                    data={chartData}
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="month"
                    />

                    <YAxis
                      domain={[
                        0,
                        100,
                      ]}
                      tickFormatter={
                        (value) =>
                          `${value}%`
                      }
                    />

                    <Tooltip
                      formatter={
                        (value) =>
                          `${value}%`
                      }
                    />

                    <Line
                      type="monotone"
                      dataKey="automation_coverage"
                      name="Automation Coverage"
                      stroke="#16a34a"
                      strokeWidth={3}
                      dot={{
                        r: 5,
                      }}
                    />

                  </LineChart>

                </ResponsiveContainer>

              </div>

            </section>


            {/* ==================================================
                MONTHLY TABLE
                ================================================== */}

            <section className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">

              <div className="p-6 border-b border-gray-200">

                <h3 className="text-lg font-semibold text-gray-900">

                  Monthly QE History

                </h3>

                <p className="text-sm text-gray-500 mt-1">

                  Historical snapshot data

                </p>

              </div>


              <div className="overflow-x-auto">

                <table className="w-full text-sm">

                  <thead className="bg-gray-50 border-b border-gray-200">

                    <tr>

                      <th className="px-5 py-3 text-left font-semibold text-gray-600">
                        Month
                      </th>

                      <th className="px-5 py-3 text-right font-semibold text-gray-600">
                        Bugs
                      </th>

                      <th className="px-5 py-3 text-right font-semibold text-gray-600">
                        SIT
                      </th>

                      <th className="px-5 py-3 text-right font-semibold text-gray-600">
                        UAT
                      </th>

                      <th className="px-5 py-3 text-right font-semibold text-gray-600">
                        PROD
                      </th>

                      <th className="px-5 py-3 text-right font-semibold text-gray-600">
                        Features
                      </th>

                      <th className="px-5 py-3 text-right font-semibold text-gray-600">
                        Test Cases
                      </th>

                      <th className="px-5 py-3 text-right font-semibold text-gray-600">
                        Automatable
                      </th>

                      <th className="px-5 py-3 text-right font-semibold text-gray-600">
                        Automated
                      </th>

                      <th className="px-5 py-3 text-right font-semibold text-gray-600">
                        Coverage
                      </th>

                    </tr>

                  </thead>


                  <tbody>

                    {[
                      ...trends,
                    ]
                      .reverse()
                      .map(
                        (item) => (

                          <tr
                            key={
                              item.id
                            }
                            className="border-b border-gray-100 hover:bg-gray-50"
                          >

                            <td className="px-5 py-4 font-medium text-gray-900">

                              {formatMonth(
                                item.snapshot_month
                              )}

                            </td>

                            <td className="px-5 py-4 text-right font-semibold">

                              {formatNumber(
                                item.total_bugs
                              )}

                            </td>

                            <td className="px-5 py-4 text-right">

                              {formatNumber(
                                item.sit_bugs
                              )}

                            </td>

                            <td className="px-5 py-4 text-right">

                              {formatNumber(
                                item.uat_bugs
                              )}

                            </td>

                            <td className="px-5 py-4 text-right text-red-600 font-semibold">

                              {formatNumber(
                                item.prod_bugs
                              )}

                            </td>

                            <td className="px-5 py-4 text-right">

                              {formatNumber(
                                item.total_features
                              )}

                            </td>

                            <td className="px-5 py-4 text-right">

                              {formatNumber(
                                item.total_test_cases
                              )}

                            </td>

                            <td className="px-5 py-4 text-right">

                              {formatNumber(
                                item.automatable_test_cases
                              )}

                            </td>

                            <td className="px-5 py-4 text-right">

                              {formatNumber(
                                item.automated_test_cases
                              )}

                            </td>

                            <td className="px-5 py-4 text-right font-semibold text-green-600">

                              {Number(
                                item.automation_coverage ||
                                0
                              ).toFixed(2)}
                              %

                            </td>

                          </tr>

                        )
                      )}

                  </tbody>

                </table>

              </div>

            </section>

          </>

        )}

      </main>

    </div>
  );
}


export default QETrends;
