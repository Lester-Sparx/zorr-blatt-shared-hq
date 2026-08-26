import fs from "node:fs";
import crypto from "node:crypto";
import { NullEngine } from "@babylonjs/core/Engines/nullEngine.js";
import { Scene } from "@babylonjs/core/scene.js";
import { SceneLoader } from "@babylonjs/core/Loading/sceneLoader.js";
import "@babylonjs/loaders/glTF/index.js";
import XMLHttpRequest from "xhr2";

globalThis.XMLHttpRequest = XMLHttpRequest;

const [glbPath = "b0-body.glb", rustReportPath = "b0-rust.json", outPath = "b0-babylon.json"] = process.argv.slice(2);

const glb = fs.readFileSync(glbPath);
const rust = JSON.parse(fs.readFileSync(rustReportPath, "utf8"));

if (glb.length < 20 || glb.subarray(0, 4).toString("ascii") !== "glTF") {
  throw new Error("B0: compiled artifact is not a GLB 2.0 binary");
}
if (rust.has_suit !== true) {
  throw new Error("B0: Rust-side compiled mesh did not report has_suit=true");
}

const engine = new NullEngine({
  renderWidth: 64,
  renderHeight: 64,
  deterministicLockstep: true,
  lockstepMaxSteps: 1,
});
const scene = new Scene(engine);
const dataUri = `data:;base64,${glb.toString("base64")}`;

const loaded = await SceneLoader.ImportMeshAsync("", "", dataUri, scene, undefined, ".glb");
const renderMeshes = loaded.meshes.filter((m) => typeof m.getTotalVertices === "function" && m.getTotalVertices() > 0);

if (renderMeshes.length === 0) {
  throw new Error("B0: Babylon loaded no renderable mesh geometry");
}

let vertexCount = 0;
let indexCount = 0;
const min = [Infinity, Infinity, Infinity];
const max = [-Infinity, -Infinity, -Infinity];

for (const mesh of renderMeshes) {
  mesh.computeWorldMatrix(true);
  vertexCount += mesh.getTotalVertices();
  indexCount += mesh.getTotalIndices();
  const box = mesh.getBoundingInfo().boundingBox;
  const mn = box.minimumWorld;
  const mx = box.maximumWorld;
  const mins = [mn.x, mn.y, mn.z];
  const maxs = [mx.x, mx.y, mx.z];
  for (let i = 0; i < 3; i += 1) {
    min[i] = Math.min(min[i], mins[i]);
    max[i] = Math.max(max[i], maxs[i]);
  }
}

const span = max.map((v, i) => v - min[i]);
const rustSpan = rust.bbox_span.map(Number);
const sortedBabylon = [...span].sort((a, b) => a - b);
const sortedRust = [...rustSpan].sort((a, b) => a - b);

const close = (a, b) => {
  const tol = Math.max(1e-4, Math.max(Math.abs(a), Math.abs(b)) * 1e-4);
  return Math.abs(a - b) <= tol;
};

if (vertexCount !== rust.vertex_count) {
  throw new Error(`B0: vertex count changed across GLB/Babylon boundary: rust=${rust.vertex_count} babylon=${vertexCount}`);
}
if (indexCount !== rust.index_count) {
  throw new Error(`B0: index count changed across GLB/Babylon boundary: rust=${rust.index_count} babylon=${indexCount}`);
}
for (let i = 0; i < 3; i += 1) {
  if (!close(sortedBabylon[i], sortedRust[i])) {
    throw new Error(`B0: bbox span mismatch at sorted axis ${i}: rust=${sortedRust[i]} babylon=${sortedBabylon[i]}`);
  }
}

const fitResults = Array.isArray(rust.fit?.results) ? rust.fit.results : [];
const maxAbsFitDeltaCm = fitResults.reduce((m, r) => Math.max(m, Math.abs(Number(r.delta_cm ?? 0))), 0);
if (fitResults.length === 0) {
  throw new Error("B0: missing explicit fit residual results");
}

const babylonPackage = JSON.parse(fs.readFileSync("node_modules/@babylonjs/core/package.json", "utf8"));
const report = {
  proof: "B0_BABYLON_BODY_COMPILER_V1",
  result: "PASS",
  babylon_version: babylonPackage.version,
  glb_bytes: glb.length,
  glb_sha256: crypto.createHash("sha256").update(glb).digest("hex"),
  render_mesh_count: renderMeshes.length,
  vertex_count: vertexCount,
  index_count: indexCount,
  bbox_min: min,
  bbox_max: max,
  bbox_span: span,
  rust_bbox_span: rustSpan,
  bbox_comparison: "PASS_AFTER_AXIS_SORT__COORDINATE_POLICY_OPEN",
  max_abs_fit_delta_cm: maxAbsFitDeltaCm,
  authority: {
    donor_params_are_character_truth: false,
    donor_skeleton_is_rest_rig: false,
    babylon_mesh_is_authority: false,
    compiled_mesh_is_derived: true,
  },
};

fs.writeFileSync(outPath, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report, null, 2));

scene.dispose();
engine.dispose();
