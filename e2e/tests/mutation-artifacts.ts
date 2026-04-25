import fs from "fs";
import path from "path";

type MutationArtifact = {
  kind: string;
  created_at: string;
  payload: Record<string, any>;
};

const reportsDir = path.join(process.cwd(), "reports");
const artifactsPath = path.join(reportsDir, "mutation-artifacts.json");

function readArtifacts(): MutationArtifact[] {
  if (!fs.existsSync(artifactsPath)) {
    return [];
  }

  try {
    const raw = fs.readFileSync(artifactsPath, "utf-8");
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function recordMutationArtifact(kind: string, payload: Record<string, any>) {
  fs.mkdirSync(reportsDir, { recursive: true });
  const artifacts = readArtifacts();
  artifacts.push({
    kind,
    created_at: new Date().toISOString(),
    payload,
  });
  fs.writeFileSync(artifactsPath, JSON.stringify(artifacts, null, 2), "utf-8");
}
