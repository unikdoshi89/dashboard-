import React from "react";
import { ArrowLeft, Calculator, Info } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

function CalculationDetails() {
  const navigate = useNavigate();
  const { projectId } = useParams();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <Calculator size={22} className="text-blue-600" />
              <h1 className="text-xl font-bold text-gray-900">
                Quality Score Calculation
              </h1>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Complete calculation logic and scoring methodology
            </p>
          </div>

          <button
            type="button"
            onClick={() => navigate(projectId ? `/?project=${projectId}` : "/")}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-white text-gray-700 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50"
          >
            <ArrowLeft size={16} />
            Back to Dashboard
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">

        <section className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900">
            Quality Confidence Score
          </h2>
          <p className="text-gray-600 mt-2 leading-7">
            The Quality Confidence Score converts each configured metric into
            a normalized score from 0 to 100, calculates a weighted score for
            each category, and then calculates the weighted overall quality
            score.
          </p>
          <div className="mt-5 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="font-semibold text-blue-900">Overall calculation</p>
            <p className="mt-2 text-blue-800 font-mono text-sm">
              Overall Score = Σ(Category Score × Category Weight) ÷ Σ(Category Weight)
            </p>
          </div>
        </section>

        <section className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900">
            1. Individual Metric Score
          </h2>
          <p className="text-gray-600 mt-2">
            Every metric is converted to a score between 0 and 100 before it
            contributes to its category.
          </p>

          <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div className="border border-gray-200 rounded-lg p-5">
              <h3 className="font-semibold text-gray-900">Higher is Better</h3>
              <div className="mt-4 space-y-3 text-sm text-gray-700">
                <p><strong>Value ≥ Target:</strong> Score = 100</p>
                <p><strong>Warning ≤ Value &lt; Target:</strong> 75 → 100 linearly</p>
                <p><strong>Critical ≤ Value &lt; Warning:</strong> 40 → 75 linearly</p>
                <p><strong>Value &lt; Critical:</strong> max(0, (Value / Critical) × 40)</p>
              </div>
              <div className="mt-4 p-4 bg-gray-50 rounded-lg font-mono text-xs leading-6">
                Score = 75 + ((Value - Warning) / (Target - Warning)) × 25
                <br />
                Score = 40 + ((Value - Critical) / (Warning - Critical)) × 35
                <br />
                Score = max(0, (Value / Critical) × 40)
              </div>
            </div>

            <div className="border border-gray-200 rounded-lg p-5">
              <h3 className="font-semibold text-gray-900">Lower is Better</h3>
              <div className="mt-4 space-y-3 text-sm text-gray-700">
                <p><strong>Value ≤ Target:</strong> Score = 100</p>
                <p><strong>Target &lt; Value ≤ Warning:</strong> 75 → 100 linearly</p>
                <p><strong>Warning &lt; Value ≤ Critical:</strong> 40 → 75 linearly</p>
                <p><strong>Value &gt; Critical:</strong> Score = 0</p>
              </div>
              <div className="mt-4 p-4 bg-gray-50 rounded-lg font-mono text-xs leading-6">
                Score = 75 + ((Warning - Value) / (Warning - Target)) × 25
                <br />
                Score = 40 + ((Critical - Value) / (Critical - Warning)) × 35
                <br />
                Value &gt; Critical → 0
              </div>
            </div>
          </div>
        </section>

        <section className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900">
            2. Special Metric Calculations
          </h2>

          <div className="mt-5 grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div className="border border-gray-200 rounded-lg p-5">
              <h3 className="font-semibold text-gray-900">Automation Coverage</h3>
              <p className="text-gray-600 mt-2">
                The actual automation percentage is used directly as the score.
              </p>
              <div className="mt-4 p-4 bg-gray-50 rounded-lg font-mono text-sm">
                Score = Automation Coverage %
              </div>
              <p className="mt-3 text-sm text-gray-600">
                86% → 86 score · 75% → 75 score · 100% → 100 score
              </p>
            </div>

            <div className="border border-gray-200 rounded-lg p-5">
              <h3 className="font-semibold text-gray-900">Production Quality</h3>
              <p className="text-gray-600 mt-2">
                Each production bug reduces the production-quality score by
                10 points.
              </p>
              <div className="mt-4 p-4 bg-gray-50 rounded-lg font-mono text-sm">
                Score = max(0, 100 - (Production Bugs × 10))
              </div>
              <p className="mt-3 text-sm text-gray-600">
                0 bugs → 100 · 1 → 90 · 2 → 80 · 10+ → 0
              </p>
            </div>
          </div>
        </section>

        <section className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900">
            3. Category Score
          </h2>
          <p className="text-gray-600 mt-2">
            Metric scores are combined using their configured metric weights.
          </p>

          <div className="mt-5 p-4 bg-gray-50 rounded-lg font-mono text-sm">
            Category Score = Σ(Metric Score × Metric Weight) ÷ Σ(Metric Weight)
          </div>

          <div className="mt-5 border border-amber-200 bg-amber-50 rounded-lg p-5">
            <div className="flex gap-3">
              <Info className="text-amber-600 flex-shrink-0" size={20} />
              <div>
                <h3 className="font-semibold text-amber-900">
                  Missing metric data
                </h3>
                <p className="text-sm text-amber-800 mt-1">
                  A configured enabled metric with no current value is treated
                  as score 0. Its positive configured weight remains in the
                  category denominator.
                </p>
                <p className="mt-2 font-mono text-sm text-amber-900">
                  Missing Metric Value → Metric Score = 0
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900">
            4. Overall Quality Confidence Score
          </h2>

          <div className="mt-5 p-4 bg-gray-50 rounded-lg font-mono text-sm">
            Overall Score = Σ(Category Score × Category Weight) ÷ Σ(Category Weight)
          </div>

          <div className="mt-5 border border-red-200 bg-red-50 rounded-lg p-5">
            <div className="flex gap-3">
              <Info className="text-red-600 flex-shrink-0" size={20} />
              <div>
                <h3 className="font-semibold text-red-900">
                  Missing category data
                </h3>
                <p className="text-sm text-red-800 mt-1">
                  A category with no usable metric data is treated as score 0.
                  Its configured positive category weight remains in the
                  overall calculation.
                </p>
                <p className="mt-2 font-mono text-sm text-red-900">
                  Missing Category Score → 0
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6">
            <h3 className="font-semibold text-gray-900">
              Example: only Test Design &amp; Coverage has data
            </h3>

            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-sm border border-gray-200">
                <thead className="bg-gray-50">
                  <tr className="border-b border-gray-200 text-left">
                    <th className="p-3">Category</th>
                    <th className="p-3">Weight</th>
                    <th className="p-3">Score</th>
                    <th className="p-3">Contribution</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-gray-100">
                    <td className="p-3">Test Design &amp; Coverage</td>
                    <td className="p-3">30%</td>
                    <td className="p-3">73</td>
                    <td className="p-3">21.90</td>
                  </tr>
                  <tr className="border-b border-gray-100">
                    <td className="p-3">Detection Capability</td>
                    <td className="p-3">15%</td>
                    <td className="p-3">0</td>
                    <td className="p-3">0</td>
                  </tr>
                  <tr className="border-b border-gray-100">
                    <td className="p-3">Automation Coverage &amp; Stability</td>
                    <td className="p-3">15%</td>
                    <td className="p-3">0</td>
                    <td className="p-3">0</td>
                  </tr>
                  <tr className="border-b border-gray-100">
                    <td className="p-3">Effectiveness</td>
                    <td className="p-3">15%</td>
                    <td className="p-3">0</td>
                    <td className="p-3">0</td>
                  </tr>
                  <tr className="border-b border-gray-100">
                    <td className="p-3">Production Quality</td>
                    <td className="p-3">15%</td>
                    <td className="p-3">0</td>
                    <td className="p-3">0</td>
                  </tr>
                  <tr>
                    <td className="p-3">Continuous Improvement</td>
                    <td className="p-3">10%</td>
                    <td className="p-3">0</td>
                    <td className="p-3">0</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="mt-4 p-5 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="font-semibold text-blue-900">
                Overall Score = 21.90
              </p>
              <p className="mt-2 font-mono text-sm text-blue-800">
                73 × 30% + 0 × 15% + 0 × 15% + 0 × 15% + 0 × 15% + 0 × 10%
                = 21.90
              </p>
            </div>
          </div>
        </section>

        <section className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900">
            5. Overall Status
          </h2>

          <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border border-green-200 bg-green-50 rounded-lg p-5">
              <p className="text-sm text-green-700">Score</p>
              <p className="text-2xl font-bold text-green-900 mt-1">≥ 80</p>
              <p className="font-semibold text-green-800 mt-2">STRONG</p>
            </div>

            <div className="border border-yellow-200 bg-yellow-50 rounded-lg p-5">
              <p className="text-sm text-yellow-700">Score</p>
              <p className="text-2xl font-bold text-yellow-900 mt-1">
                60 – 79.99
              </p>
              <p className="font-semibold text-yellow-800 mt-2">MODERATE</p>
            </div>

            <div className="border border-red-200 bg-red-50 rounded-lg p-5">
              <p className="text-sm text-red-700">Score</p>
              <p className="text-2xl font-bold text-red-900 mt-1">&lt; 60</p>
              <p className="font-semibold text-red-800 mt-2">LOW</p>
            </div>
          </div>

          <div className="mt-5 p-4 bg-gray-50 rounded-lg text-sm text-gray-700">
            Metrics with weight ≤ 0 do not contribute to their category.
          </div>
        </section>
      </main>
    </div>
  );
}

export default CalculationDetails;
