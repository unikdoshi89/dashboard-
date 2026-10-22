import axios from "axios";
import apiClient from "./client";

const api = axios.create({
  baseURL: "http://localhost:8000/api",
});


// ==================================================
// Get Automation Details
// ==================================================

export async function getAutomationDetails(
  projectId
) {
  const response = await apiClient.get(
    `/projects/${projectId}/automation`
  );

  return response.data;
}


// ==================================================
// Create Release
// ==================================================

export async function createAutomationRelease(
  projectId,
  payload
) {
  const response = await api.post(
    `/projects/${projectId}/automation/releases`,
    payload
  );

  return response.data;
}


// ==================================================
// Add POD
// ==================================================

export async function createAutomationPod(
  projectId,
  releaseId,
  payload
) {
  const response = await apiClient.post(
    `/projects/automation/releases/${releaseId}/details`,
    payload
  );

  return response.data;
}


// ==================================================
// Update POD
// ==================================================

export async function updateAutomationPod(
  detailId,
  payload
) {
  const response = await api.put(
    `/projects/automation/details/${detailId}`,
    payload
  );

  return response.data;
}


// ==================================================
// Delete POD
// ==================================================

export async function deleteAutomationPod(
  detailId
) {
  const response = await api.delete(
    `/projects/automation/details/${detailId}`
  );

  return response.data;
}

export async function getAutomationSummary(projectId) {
  const response = await apiClient.get(
    `/projects/${projectId}/automation/summary`
  );

  return response.data;
}
