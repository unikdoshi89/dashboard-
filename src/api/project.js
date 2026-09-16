import apiClient from "./client";

export async function getProjects() {
  const response = await apiClient.get("/projects");
  return response.data;
}

export async function getProjectDashboard(projectId) {
  const response = await apiClient.get(
    `/projects/${projectId}/dashboard`
  );

  return response.data;
}

export async function getAvailableMetrics(projectId) {
  const response = await apiClient.get(
    `/projects/${projectId}/available-metrics`
  );

  return response.data;
}



export async function createProject(
  payload
) {
  const response = await apiClient.post(
    "/projects",
    payload
  );

  return response.data;
}



export async function addMetric(
  projectId,
  payload
) {
  const response = await apiClient.post(
    `/projects/projects/${projectId}/metrics`,
    payload
  );

  return response.data;
}

export async function getQualityScore(projectId) {
  const response = await apiClient.get(
    `/projects/projects/${projectId}/quality-score`
  );

  return response.data;
}

export async function getReleases(projectId) {
  const response = await apiClient.get(
    `/projects/${projectId}/releases`
  );

  return response.data;
}

export async function downloadProjectPdf(projectId) {
  const response = await apiClient.get(
    `/projects/projects/${projectId}/report/pdf`,
    {
      responseType: "blob",
    }
  );

  return response.data;
}

export async function uploadAutomationExcel(
  projectId,
  file
) {
  const formData = new FormData();

  formData.append("file", file);

  const response = await apiClient.post(
    `/projects/projects/${projectId}/automation/upload`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
}

export async function getLatestAutomationUpload(
  projectId
) {
  const response = await apiClient.get(
    `/projects/projects/${projectId}/automation/uploads/latest`
  );

  return response.data;
}

export async function getProjectHtmlReport(
  projectId
) {
  const response = await apiClient.get(
    `/projects/projects/${projectId}/report/html`,
    {
      responseType: "text",
    }
  );

  return response.data;
}
