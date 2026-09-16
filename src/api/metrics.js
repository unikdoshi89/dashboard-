import apiClient from "./client";

export async function updateMetricValue(
  projectMetricId,
  payload
) {
  const response = await apiClient.put(
    `/metrics/${projectMetricId}/value`,
    payload
  );

  return response.data;
}

export async function getMetricHistory(
  projectMetricId
) {
  const response = await apiClient.get(
    `/metrics/${projectMetricId}/history`
  );

  return response.data;
}

export async function deleteMetric(
  projectMetricId
) {
  const response = await apiClient.delete(
    `/metrics/${projectMetricId}`
  );

  return response.data;
}
