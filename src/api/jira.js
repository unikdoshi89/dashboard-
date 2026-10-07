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
  allPage = 1,
  uatPage = 1,
  prodPage = 1,
  perPage = 50
) {
  const response = await apiClient.get(
    `/projects/${projectId}/jira/bugs`,
    {
      params: {
        all_page: allPage,
        uat_page: uatPage,
        prod_page: prodPage,
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
