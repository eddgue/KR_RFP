// Barrel for the typed API client.
export * from "./types";
export { ApiError, apiFetch, apiUpload, apiDownload } from "./client";
export type { ApiErrorCode } from "./client";
export { login, logout, me } from "./auth";
export { listRuns, createRun, getRun } from "./runs";
export {
  listRunFiles,
  downloadRunFile,
  downloadRunArchive,
  uploadSetup,
  generateTemplate,
  importBids,
  listBids,
} from "./intake";
export type { ImportBidsArgs } from "./intake";
export {
  runAnalysis,
  listAnalyses,
  getScenarioComparison,
  getScenarioDetail,
  freezeAward,
} from "./alignment";
