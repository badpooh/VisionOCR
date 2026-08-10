import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const taskDir = "C:/PNT/61.AI/VisionOCR/outputs/cmc-phases-20260722";
const inputPath = "C:/PNT/61.AI/VisionOCR/config/A2700/Source_Test_A2700M.xlsx";
const outputPath = path.join(taskDir, "Source_Test_A2700M.xlsx");
const mode = process.argv[2] || "inspect";
const sourcePath = mode === "verify" ? outputPath : inputPath;
const phaseHeaders = ["Va_deg", "Vb_deg", "Vc_deg", "Ia_deg", "Ib_deg", "Ic_deg"];
const defaultPhases = [0, 240, 120, 0, 240, 120];

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(sourcePath));
const cmc = workbook.worksheets.getItem("CMC");
const cmcValues = cmc.getUsedRange(true).values;
const lastRow = cmcValues.length;
const beforeRange = `A1:L${lastRow}`;

console.log((await workbook.inspect({
  kind: "table",
  sheetId: "CMC",
  range: `A1:L${Math.min(lastRow, 18)}`,
  include: "values,formulas",
  tableMaxRows: 18,
  tableMaxCols: 12,
  maxChars: 8000,
})).ndjson);
console.log((await workbook.inspect({
  kind: "computedStyle",
  sheetId: "CMC",
  range: "A1:L4",
  maxChars: 4000,
})).ndjson);

if (mode === "inspect") {
  const preview = await workbook.render({
    sheetName: "CMC",
    range: beforeRange,
    scale: 0.8,
    format: "png",
  });
  await fs.writeFile(
    path.join(taskDir, "cmc_before.png"),
    new Uint8Array(await preview.arrayBuffer()),
  );
} else if (mode === "edit") {
  const existingHeaders = cmcValues[0].map((value) => String(value ?? "").trim());
  if (phaseHeaders.some((header) => existingHeaders.includes(header))) {
    throw new Error("CMC phase columns already exist");
  }

  const phaseRows = [phaseHeaders];
  for (let rowIndex = 1; rowIndex < lastRow; rowIndex += 1) {
    const tcId = String(cmcValues[rowIndex][0] ?? "").trim();
    phaseRows.push(tcId ? [...defaultPhases] : [null, null, null, null, null, null]);
  }
  cmc.getRange(`M1:R${lastRow}`).values = phaseRows;
  cmc.getRange(`M2:R${lastRow}`).format.numberFormat = "0.###";
  cmc.getRange("M:R").format.columnWidth = 10;

  const guide = workbook.worksheets.getItem("Guide");
  guide.getRange("D4").values = [[
    "이 값은 판정 대상이 아닙니다. 위상 컬럼은 degree 단위이며 빈 셀은 0/240/120을 사용합니다.",
  ]];

  console.log((await workbook.inspect({
    kind: "table",
    sheetId: "CMC",
    range: `A1:R${Math.min(lastRow, 18)}`,
    include: "values,formulas",
    tableMaxRows: 18,
    tableMaxCols: 18,
    maxChars: 12000,
  })).ndjson);
  console.log((await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 300 },
    summary: "final formula error scan",
  })).ndjson);

  const cmcPreview = await workbook.render({
    sheetName: "CMC",
    range: `A1:R${lastRow}`,
    scale: 0.65,
    format: "png",
  });
  await fs.writeFile(
    path.join(taskDir, "cmc_after.png"),
    new Uint8Array(await cmcPreview.arrayBuffer()),
  );
  const guidePreview = await workbook.render({
    sheetName: "Guide",
    autoCrop: "all",
    scale: 1,
    format: "png",
  });
  await fs.writeFile(
    path.join(taskDir, "guide_after.png"),
    new Uint8Array(await guidePreview.arrayBuffer()),
  );

  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(outputPath);
  console.log(JSON.stringify({ outputPath, phaseRows: phaseRows.length - 1 }));
} else if (mode === "verify") {
  console.log((await workbook.inspect({
    kind: "sheet",
    include: "id,name",
    maxChars: 4000,
  })).ndjson);
  console.log((await workbook.inspect({
    kind: "table",
    sheetId: "CMC",
    range: `K1:R${Math.min(lastRow, 18)}`,
    include: "values,formulas",
    tableMaxRows: 18,
    tableMaxCols: 8,
    maxChars: 8000,
  })).ndjson);

  for (const sheetName of [
    "TestCases", "SetupModbus", "CMC", "MeasurementModbus",
    "Navigation", "Expected", "Guide",
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
