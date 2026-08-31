#!/usr/bin/env node
import fs from "node:fs";
import process from "node:process";
import "@babylonjs/core/Culling/ray.js";
import { ArcRotateCamera, Engine, Frustum, Matrix, MeshBuilder, NullEngine, Ray, Scene, Vector3 } from "@babylonjs/core";

function die(message, extra = {}) {
  const out = { schema: "BABYLON_CAMERA_SOLVER_PROOF_R03_NATIVE", runtime_ok: false, error: String(message), ...extra };
  process.stderr.write(`${JSON.stringify(out, null, 2)}\n`);
  process.exit(2);
}
const vec3 = (a) => new Vector3(Number(a[0]), Number(a[1]), Number(a[2]));
const toArray = (v) => [v.x, v.y, v.z];
const inputPath = process.argv[2];
const outputPath = process.argv[3];
if (!inputPath || !outputPath) die("Usage: node zorr_babylon_native_probe_r03.mjs <native_input.json> <native_result.json>");
let payload;
try { payload = JSON.parse(fs.readFileSync(inputPath, "utf8")); } catch (err) { die(`Cannot read/parse input: ${err}`); }
const W = Number(payload.viewport?.width ?? payload.width ?? 1920);
const H = Number(payload.viewport?.height ?? payload.height ?? 1080);
let alpha, beta, radius, fov, target;
if (Array.isArray(payload.theta) && payload.theta.length === 4) {
  const [a, b, rho, fv] = payload.theta.map(Number);
  alpha = a; beta = b; radius = Math.exp(rho); fov = fv; target = vec3(payload.target ?? [0,0,0]);
} else if (payload.camera) {
  alpha = Number(payload.camera.alpha); beta = Number(payload.camera.beta); radius = Number(payload.camera.radius);
  fov = Number(payload.camera.fov); target = vec3(payload.camera.target ?? [0,0,0]);
} else die("payload must contain theta or camera");
const points = (payload.points_world ?? payload.points ?? []).map(vec3);
const engine = new NullEngine({ renderWidth: W, renderHeight: H, textureSize: Math.max(W,H), deterministicLockstep: true, lockstepMaxSteps: 4 });
const scene = new Scene(engine);
scene.useRightHandedSystem = false;
const camera = new ArcRotateCamera("camera_r03", alpha, beta, radius, target, scene);
camera.fov = fov;
camera.minZ = Number(payload.minZ ?? payload.camera?.minZ ?? 0.1);
camera.maxZ = Number(payload.maxZ ?? payload.camera?.maxZ ?? 1000.0);
scene.activeCamera = camera;
camera.getViewMatrix(true); camera.getProjectionMatrix(true);
const transform = camera.getTransformationMatrix();
const view = camera.getViewMatrix(); const projection = camera.getProjectionMatrix();
const viewport = camera.viewport.toGlobal(W,H); const worldIdentity = Matrix.Identity();
const projectedVectors = points.map((p) => Vector3.Project(p, worldIdentity, transform, viewport));
const projected = projectedVectors.map((p) => [p.x,p.y]);
const projectedDepth = projectedVectors.map((p) => p.z);
const unprojected = projectedVectors.map((p) => Vector3.Unproject(p,W,H,worldIdentity,view,projection));
const unprojectError = unprojected.map((p,i) => Vector3.Distance(p,points[i]));
let occlusion = { requested:false, exact_babylon_pick:null };
if (payload.occlusion_case) {
  const occ = payload.occlusion_case; const center = vec3(occ.box_center); const size = vec3(occ.box_size);
  const box = MeshBuilder.CreateBox("r03_occluder", {width:size.x,height:size.y,depth:size.z}, scene);
  box.position.copyFrom(center); box.computeWorldMatrix(true); box.refreshBoundingInfo();
  const protectedPoint = vec3(occ.protected_point); const origin = camera.globalPosition.clone();
  const direction = protectedPoint.subtract(origin); const protectedDistance = direction.length(); direction.normalize();
  const ray = new Ray(origin,direction,protectedDistance); const pick = scene.pickWithRay(ray,(mesh)=>mesh===box,false);
  occlusion = { requested:true, exact_babylon_pick:Boolean(pick?.hit), picked_mesh:pick?.pickedMesh?.name ?? null,
    picked_distance:pick?.hit ? Number(pick.distance):null, protected_distance:protectedDistance,
    occluded_before_protected_point:Boolean(pick?.hit && pick.distance < protectedDistance) };
}
let frustum = { requested:false, exact_babylon_in_frustum:null };
if (payload.frustum_case) {
  const fc = payload.frustum_case; const center = vec3(fc.box_center); const size = vec3(fc.box_size);
  const box = MeshBuilder.CreateBox("r03_frustum_box", {width:size.x,height:size.y,depth:size.z}, scene);
  box.position.copyFrom(center); box.computeWorldMatrix(true); box.refreshBoundingInfo();
  const planes = Frustum.GetPlanes(camera.getTransformationMatrix());
  frustum = { requested:true, exact_babylon_in_frustum:Boolean(box.isInFrustum(planes)) };
}
const nativePosition = camera.globalPosition.clone();
const out = { schema:"BABYLON_CAMERA_SOLVER_PROOF_R03_NATIVE", runtime_ok:true, engine_version:Engine.Version ?? null,
  expected_package_version:"9.23.0", source_binding_commit:"38ed028f40722504a215002fbc2fa89a2c89cf5d",
  viewport:{width:W,height:H}, camera:{alpha,beta,radius,fov,target:toArray(target),native_global_position:toArray(nativePosition),minZ:camera.minZ,maxZ:camera.maxZ},
  projected, projected_depth:projectedDepth, unproject_roundtrip_max:unprojectError.length ? Math.max(...unprojectError):0,
  max_unproject_roundtrip_world_error:unprojectError.length ? Math.max(...unprojectError):0, occlusion, frustum };
fs.writeFileSync(outputPath, `${JSON.stringify(out,null,2)}\n`, "utf8");
process.stdout.write(`${JSON.stringify(out,null,2)}\n`); scene.dispose(); engine.dispose();
