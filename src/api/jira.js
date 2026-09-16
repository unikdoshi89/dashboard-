import apiClient from "./client";


export async function getJiraConfig(projectId) {
  const response = await apiClient.get(
    `/projects/${projectId}/jira/config`
  );

  return response.data;
}


export async function saveJiraConfig(
  projectId,
  payload
) {
  const response = await apiClient.post(
    `/projects/${projectId}/jira/config`,
    payload
  );

  return response.data;
}


export async function testJiraConnection(
  projectId
) {
  const response = await apiClient.post(
    `/projects/${projectId}/jira/test-connection`
  );

  return response.data;
}


export async function getJiraBugs(
  projectId,
  search = "",
  page = 1,
  perPage = 200
) {
  const response = await apiClient.get(
    `/projects/${projectId}/jira/bugs`,
    {
      params: {
        page,
        per_page: perPage,
        ...(search ? { search } : {}),
      },
    }
  );

  return response.data;
}

export async function getJiraFeatures(
  projectId,
  page = 1,
  perPage = 20,
  search = ""
) {
  const response = await apiClient.get(
    `/projects/${projectId}/jira/features`,
    {
      params: {
        page,
        per_page: perPage,
        search,
      },
    }
  );

  return response.data;
}
