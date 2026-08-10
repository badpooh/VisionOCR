import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const taskDir = "C:/PNT/61.AI/VisionOCR/outputs/unit-options-20260721";
const inputPath = "C:/PNT/61.AI/VisionOCR/config/A2700/Source_Test_A2700M.xlsx";
const outputPath = path.join(taskDir, "Source_Test_A2700M.xlsx");
const mode = process.argv[2] || "inspect";
const sourcePath = mode === "verify" ? outputPath : inputPath;

const input = await FileBlob.load(sourcePath);
const workbook = await SpreadsheetFile.importXlsx(input);
const sheet = workbook.worksheets.getItem("Expected");
const used = sheet.getUsedRange(true);
const values = used.values;
const headers = values[0].map((value) => String(value ?? "").trim());
const tcColumn = headers.indexOf("TC_ID");
const unitColumn = headers.indexOf("Unit");

if (tcColumn < 0 || unitColumn < 0) {
  throw new Error("Expected sheet is missing TC_ID or Unit header");
}

const targetRows = [];
for (let rowIndex = 1; rowIndex < values.length; rowIndex += 1) {
  const tcId = String(values[rowIndex][tcColumn] ?? "").trim();
  if (tcId.startsWith("A27_SPEC-TC0022")) {
    targetRows.push(rowIndex);
  }
}

if (targetRows.length === 0) {
  throw new Error("No TC0022 Expected rows found");
}

const firstExcelRow = targetRows[0] + 1;
const lastExcelRow = targetRows[targetRows.length - 1] + 1;
const inspectRange = `A${Math.max(1, firstExcelRow - 1)}:L${lastExcelRow + 1}`;

console.log((await workbook.inspect({
  kind: "table",
  sheetId: "Expected",
  range: inspectRange,
  include: "values,formulas",
  tableMaxRows: 80,
  tableMaxCols: 12,
  maxChars: 12000,
})).ndjson);
console.log((await workbook.inspect({
  kind: "computedStyle",
  sheetId: "Expected",
  range: inspectRange,
  maxChars: 3000,
})).ndjson);

if (mode === "edit") {
  let changed = 0;
  for (const rowIndex of targetRows) {
    const current = String(values[rowIndex][unitColumn] ?? "").trim();
    if (current === "w") {
      sheet.getCell(rowIndex, unitColumn).values = [["w|W"]];
      changed += 1;
    }
  }
  console.log(JSON.stringify({ changed, outputPath }));

  const errors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 300 },
    summary: "final formula error scan",
  });
  console.log(errors.ndjson);

  console.log((await workbook.inspect({
    kind: "table",
    sheetId: "Expected",
    range: inspectRange,
    include: "values,formulas",
    tableMaxRows: 80,
    tableMaxCols: 12,
    maxChars: 12000,
  })).ndjson);

  const after = await workbook.render({
    sheetName: "Expected",
    range: inspectRange,
    scale: 1.5,
    format: "png",
  });
  await fs.writeFile(
    path.join(taskDir, "expected_after.png"),
    new Uint8Array(await after.arrayBuffer()),
  );

  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(outputPath);
} else {
  const before = await workbook.render({
    sheetName: "Expected",
    range: inspectRange,
    scale: 1.5,
    format: "png",
  });
  await fs.writeFile(
    path.join(taskDir, mode === "verify" ? "expected_verify.png" : "expected_before.png"),
    new Uint8Array(await before.arrayBuffer()),
  );

  if (mode === "verify") {
    console.log((await workbook.inspect({
      kind: "sheet",
      include: "id,name",
      maxChars: 4000,
    })).ndjson);
    for (const sheetName of [
      "TestCases",
      "SetupModbus",
      "CMC",
      "MeasurementModbus",
      "Navigation",
      "Expected",
      "Guide",
    ]) {
      const preview = await workbook.render({
        sheetName,
        autoCrop: "all",
        scale: 0.5,
        format: "png",
      });
      await fs.writeFile(
        path.join(taskDir, `verify_${sheetName}.png`),
        new Uint8Array(await preview.arrayBuffer()),
      );
    }
  }
}
