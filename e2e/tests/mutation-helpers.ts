export function mutationsEnabled() {
  return process.env.E2E_ENABLE_MUTATIONS === "true";
}
