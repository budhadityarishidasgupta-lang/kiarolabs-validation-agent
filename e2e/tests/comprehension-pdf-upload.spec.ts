import { expect, test } from "@playwright/test";

import { mutationsEnabled } from "./mutation-helpers";
import { recordMutationArtifact } from "./mutation-artifacts";

const API_BASE = "https://kiarolabs-membership-service.onrender.com";

function buildSimplePdf(lines: string[]): Buffer {
  const escapePdfText = (value: string) =>
    value.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");

  const contentLines = [
    "BT",
    "/F1 12 Tf",
    "72 720 Td",
    ...lines.flatMap((line, index) =>
      index === 0
        ? [`(${escapePdfText(line)}) Tj`]
        : ["0 -18 Td", `(${escapePdfText(line)}) Tj`],
    ),
    "ET",
  ];
  const stream = contentLines.join("\n");

  const objects = [
    "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj",
    "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj",
    "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj",
    "4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj",
    `5 0 obj\n<< /Length ${Buffer.byteLength(stream, "utf-8")} >>\nstream\n${stream}\nendstream\nendobj`,
  ];

  let pdf = "%PDF-1.4\n";
  const offsets = [0];
  for (const object of objects) {
    offsets.push(Buffer.byteLength(pdf, "utf-8"));
    pdf += `${object}\n`;
  }

  const xrefOffset = Buffer.byteLength(pdf, "utf-8");
  pdf += `xref\n0 ${objects.length + 1}\n`;
  pdf += "0000000000 65535 f \n";
  for (let i = 1; i < offsets.length; i += 1) {
    pdf += `${String(offsets[i]).padStart(10, "0")} 00000 n \n`;
  }
  pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;
  return Buffer.from(pdf, "utf-8");
}

test("admin ingestion can upload a comprehension PDF and surface the new passage", async ({ page, request }) => {
  test.skip(!mutationsEnabled(), "Mutation tests are disabled for scheduled safety.");

  const uniqueSuffix = Date.now();
  const paperCode = `E2E_PDF_${uniqueSuffix}`;
  const expectedTitle = `${paperCode} Passage 1`;

  await page.goto("/admin");
  await page.getByRole("tab", { name: "Comprehension" }).click();
  await expect(page.getByText("Comprehension Content Management")).toBeVisible({ timeout: 15000 });

  const token = await page.evaluate(() => window.localStorage.getItem("access_token"));
  expect(token, "Missing admin access token").toBeTruthy();

  const pdfBuffer = buildSimplePdf([
    "Passage 1",
    "A short passage for PDF ingestion validation.",
    "1. What is this test checking?",
    "2. That PDF ingestion works end to end.",
  ]);

  const uploadResponse = await request.post(`${API_BASE}/admin/ingestion/comprehension/upload`, {
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${token}`,
    },
    multipart: {
      paper_code: paperCode,
      file: {
        name: `${paperCode}.pdf`,
        mimeType: "application/pdf",
        buffer: pdfBuffer,
      },
    },
  });

  const uploadRawText = await uploadResponse.text();
  let uploadPayload: any = {};
  try {
    uploadPayload = uploadRawText ? JSON.parse(uploadRawText) : {};
  } catch {
    uploadPayload = { raw: uploadRawText };
  }

  expect(
    uploadResponse.ok(),
    JSON.stringify({
      status: uploadResponse.status(),
      statusText: uploadResponse.statusText(),
      body: uploadPayload,
    }),
  ).toBeTruthy();

  await page.reload({ waitUntil: "domcontentloaded" });
  await page.getByRole("tab", { name: "Comprehension" }).click();
  await expect(page.getByText(expectedTitle)).toBeVisible({ timeout: 15000 });

  recordMutationArtifact("comprehension_pdf_upload", {
    paper_code: paperCode,
    title: expectedTitle,
  });
});
