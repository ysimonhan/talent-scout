import { defineRailway, github, project, service } from "railway/iac";

export const partial = "talent-scout-apps";

export default defineRailway(() => {
  const backend = service("talent-scout", {
    source: github("ysimonhan/talent-scout", {
      branch: "main",
      rootDirectory: "/",
      checkSuites: false,
    }),
    build: {
      buildEnvironment: "V3",
      builder: "DOCKERFILE",
      dockerfilePath: "/Dockerfile",
      watchPatterns: ["backend/**", "pyproject.toml", "uv.lock", "main.py"],
    },
    start: "sh -c 'uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}'",
    healthcheck: "/api/health",
    healthcheckTimeout: 300,
    replicas: { "europe-west4-drams3a": 1 },
    deploy: {
      // Railway normalizes default restartPolicyType ("ON_FAILURE") and default maxRetries (10) to null.
    },
  });

  const frontend = service("talent-scout-demo", {
    source: github("ysimonhan/talent-scout", {
      branch: "main",
      rootDirectory: "/frontend",
      checkSuites: false,
    }),
    build: {
      buildEnvironment: "V3",
      builder: "RAILPACK",
      buildCommand: "npm install && npm run build",
      watchPatterns: ["frontend/**"],
    },
    start: "npm run preview -- --host 0.0.0.0 --port $PORT",
    healthcheck: "/",
    healthcheckTimeout: 300,
    replicas: { "europe-west4-drams3a": 1 },
    deploy: {
      // Railway normalizes default restartPolicyType ("ON_FAILURE") and default maxRetries (10) to null.
    },
    networking: {
      privateNetworkEndpoint: "glorious-wisdom",
    },
  });

  return project("talent-scout", {
    variables: { managed: false },
    resources: [backend, frontend],
  });
});
