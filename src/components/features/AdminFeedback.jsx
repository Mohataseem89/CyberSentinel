import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import {
  getAllFeedback,
  getFeedbackStats,
  approveFeedback,
  rejectFeedback,
  exportApprovedFeedback,
  retrainModel
} from "../../services/api";

export default function AdminFeedback() {
  const [feedbackList, setFeedbackList] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    approved: 0,
    rejected: 0,
  });
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [retraining, setRetraining] = useState(false);

  const loadFeedback = async () => {
    try {
      setLoading(true);

      const [statsData, feedbackData] = await Promise.all([
        getFeedbackStats(),
        getAllFeedback(filter === "all" ? "" : filter),
      ]);

      setStats({
        total: statsData.total || 0,
        pending: statsData.pending || 0,
        approved: statsData.approved || 0,
        rejected: statsData.rejected || 0,
      });

      setFeedbackList(feedbackData.feedback || []);
    } catch (error) {
      console.error("Failed to load feedback:", error);
      toast.error("Failed to load feedback");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFeedback();
  }, [filter]);

  const handleApprove = async (id) => {
    try {
      await approveFeedback(id);
      toast.success("Feedback approved");
      loadFeedback();
    } catch (error) {
      console.error("Approve failed:", error);
      toast.error("Failed to approve feedback");
    }
  };

  const handleReject = async (id) => {
    try {
      await rejectFeedback(id);
      toast.success("Feedback rejected");
      loadFeedback();
    } catch (error) {
      console.error("Reject failed:", error);
      toast.error("Failed to reject feedback");
    }
  };

  const handleRetrain = async () => {
    try {
      setRetraining(true);
      toast.loading("Retraining model...", { id: "retrain" });

      const result = await retrainModel();

      console.log("Retrain result:", result);

      toast.success("Model retrained successfully", { id: "retrain" });
    } catch (error) {
      console.error("Retrain failed:", error);
      toast.error(error.message || "Failed to retrain model", { id: "retrain" });
    } finally {
      setRetraining(false);
    }
  };

  if (loading) {
    return <div className="p-8">Loading feedback...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-10">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-start justify-between mb-10">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Feedback Review Panel</h1>
            <p className="text-gray-600">
              Review user-submitted feedback before adding it to model-improvement data.
            </p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={loadFeedback}
              className="bg-blue-600 text-white px-5 py-3 rounded-lg hover:bg-blue-700"
            >
              Refresh
            </button>

            <button
              onClick={handleRetrain}
              disabled={retraining}
              className={`px-5 py-3 rounded-lg text-white ${
                retraining
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-purple-600 hover:bg-purple-700"
              }`}
            >
              {retraining ? "Retraining..." : "Retrain Model"}
            </button>

            <button
              onClick={exportApprovedFeedback}
              className="bg-blue-600 text-white px-5 py-3 rounded-lg hover:bg-blue-700"
            >
              Export Approved CSV
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
          <div className="bg-white rounded-xl shadow p-6">
            <p className="text-gray-500 mb-2">Total Feedback</p>
            <h2 className="text-4xl font-bold">{stats.total}</h2>
          </div>
          <div className="bg-white rounded-xl shadow p-6">
            <p className="text-gray-500 mb-2">Pending</p>
            <h2 className="text-4xl font-bold text-yellow-600">{stats.pending}</h2>
          </div>
          <div className="bg-white rounded-xl shadow p-6">
            <p className="text-gray-500 mb-2">Approved</p>
            <h2 className="text-4xl font-bold text-green-600">{stats.approved}</h2>
          </div>
          <div className="bg-white rounded-xl shadow p-6">
            <p className="text-gray-500 mb-2">Rejected</p>
            <h2 className="text-4xl font-bold text-red-600">{stats.rejected}</h2>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold">
              Submitted Feedback ({feedbackList.length})
            </h2>

            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="border rounded-lg px-4 py-2"
            >
              <option value="all">All</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>

          {feedbackList.length === 0 ? (
            <p className="text-gray-500 text-center py-12">No feedback found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left">
                    <th className="py-3">ID</th>
                    <th className="py-3">URL</th>
                    <th className="py-3">Category</th>
                    <th className="py-3">Actual</th>
                    <th className="py-3">Prediction</th>
                    <th className="py-3">Status</th>
                    <th className="py-3">Description</th>
                    <th className="py-3">Created</th>
                    <th className="py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {feedbackList.map((item) => (
                    <tr key={item.id} className="border-b align-top">
                      <td className="py-4">{item.id}</td>
                      <td className="py-4 break-all max-w-[220px]">{item.url}</td>
                      <td className="py-4">{item.category}</td>
                      <td className="py-4">{item.actual_threat || "-"}</td>
                      <td className="py-4">{item.our_prediction || "-"}</td>
                      <td className="py-4">{item.status}</td>
                      <td className="py-4">{item.description || "-"}</td>
                      <td className="py-4">
                        {item.created_at ? new Date(item.created_at).toLocaleString() : "-"}
                      </td>
                      <td className="py-4">
                        {item.status === "pending" ? (
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleApprove(item.id)}
                              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleReject(item.id)}
                              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
                            >
                              Reject
                            </button>
                          </div>
                        ) : (
                          <span className="text-gray-400">No actions</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}