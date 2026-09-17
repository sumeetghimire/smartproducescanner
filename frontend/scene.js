// Small line-art 3D scanner visual. Deliberately not a glossy/game-like
// render -- thin wireframe "specimen" shapes on a transparent background,
// matching the ink-on-paper aesthetic of the rest of the page. Two shapes
// (apple, banana) idle together; scanning speeds them up and adds a sweep
// line; a result settles on the matched shape, tinted by ripeness.
import * as THREE from "./vendor/three.module.js";

const RIPENESS_COLORS = {
  unripe: 0x5f6b3a,
  ripe: null, // use the base accent colour
  overripe: 0x7a3b28,
};

function currentAccentColor() {
  const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  return dark ? 0xd1a06b : 0x6a4326;
}

const APPLE_RADIUS = 0.5;

function buildAppleLines(color) {
  const geometry = new THREE.SphereGeometry(APPLE_RADIUS, 14, 10);
  geometry.scale(1, 0.88, 1);
  const maxY = APPLE_RADIUS * 0.88;
  const pullStart = maxY * 0.75;
  const pos = geometry.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i);
    if (y > pullStart) {
      // pull the top pole inward to suggest the apple's stem dimple
      const pull = (y - pullStart) * 0.6;
      pos.setY(i, y - pull);
    }
  }
  geometry.computeVertexNormals();

  const edges = new THREE.EdgesGeometry(geometry, 1);
  const material = new THREE.LineBasicMaterial({
    color,
    transparent: true,
    opacity: 0.6,
  });
  const lines = new THREE.LineSegments(edges, material);

  // stem
  const stemGeom = new THREE.CylinderGeometry(0.014, 0.022, 0.16, 5);
  const stemEdges = new THREE.EdgesGeometry(stemGeom, 1);
  const stem = new THREE.LineSegments(stemEdges, material);
  stem.position.y = maxY * 0.98;
  lines.add(stem);

  return lines;
}

function buildBananaLines(color) {
  const curve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-0.42, -0.32, 0),
    new THREE.Vector3(-0.24, 0.02, 0.05),
    new THREE.Vector3(0.02, 0.24, 0.03),
    new THREE.Vector3(0.28, 0.18, -0.03),
    new THREE.Vector3(0.46, -0.04, -0.05),
  ]);
  const geometry = new THREE.TubeGeometry(curve, 24, 0.1, 6, false);
  const edges = new THREE.EdgesGeometry(geometry, 1);
  const material = new THREE.LineBasicMaterial({
    color,
    transparent: true,
    opacity: 0.6,
  });
  return new THREE.LineSegments(edges, material);
}

function buildSweepLine(color) {
  const geometry = new THREE.RingGeometry(0.01, 0.75, 24, 1);
  const edges = new THREE.EdgesGeometry(geometry, 1);
  const material = new THREE.LineBasicMaterial({
    color,
    transparent: true,
    opacity: 0,
  });
  const ring = new THREE.LineSegments(edges, material);
  ring.rotation.x = Math.PI / 2;
  return ring;
}

export function initScanner(canvas) {
  if (!canvas || !window.WebGLRenderingContext) return null;

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  } catch (e) {
    return null;
  }

  const size = 168;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(size, size, false);
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(36, 1, 0.1, 10);
  camera.position.set(0, 0.1, 3.7);

  let accent = currentAccentColor();
  const apple = buildAppleLines(accent);
  const banana = buildBananaLines(accent);
  const APPLE_X = -0.56;
  const BANANA_X = 0.56;
  apple.position.x = APPLE_X;
  banana.position.x = BANANA_X;
  const sweep = buildSweepLine(accent);

  const group = new THREE.Group();
  group.add(apple, banana, sweep);
  scene.add(group);

  let state = "idle"; // idle | scanning | result
  let resultLabel = null;
  let sweepY = -1.2;
  let clock = new THREE.Clock();
  let rafId = null;

  const targetOpacity = { apple: 0.6, banana: 0.6, sweep: 0 };
  const targetColor = { apple: new THREE.Color(accent), banana: new THREE.Color(accent) };
  const targetX = { apple: APPLE_X, banana: BANANA_X };

  function setState(next, options = {}) {
    state = next;
    resultLabel = options.label || null;

    if (state === "idle") {
      targetOpacity.apple = 0.55;
      targetOpacity.banana = 0.55;
      targetOpacity.sweep = 0;
      targetColor.apple.set(accent);
      targetColor.banana.set(accent);
      targetX.apple = APPLE_X;
      targetX.banana = BANANA_X;
    } else if (state === "scanning") {
      targetOpacity.apple = 0.55;
      targetOpacity.banana = 0.55;
      targetOpacity.sweep = 0.7;
      targetColor.apple.set(accent);
      targetColor.banana.set(accent);
      targetX.apple = APPLE_X;
      targetX.banana = BANANA_X;
    } else if (state === "result") {
      const winner = resultLabel === "banana" ? "banana" : "apple";
      const loser = winner === "banana" ? "apple" : "banana";
      targetOpacity[winner] = 0.9;
      targetOpacity[loser] = 0.0;
      targetOpacity.sweep = 0;
      targetX[winner] = 0;
      const ripenessColor = RIPENESS_COLORS[options.ripeness];
      targetColor[winner].set(ripenessColor ?? accent);
    }
  }

  function handleThemeChange() {
    accent = currentAccentColor();
    if (state !== "result") {
      targetColor.apple.set(accent);
      targetColor.banana.set(accent);
    }
    sweep.material.color.set(accent);
  }
  const themeQuery = window.matchMedia("(prefers-color-scheme: dark)");
  themeQuery.addEventListener?.("change", handleThemeChange);

  function animate() {
    rafId = requestAnimationFrame(animate);
    const dt = Math.min(clock.getDelta(), 0.05);

    const idleSpeed = 0.18;
    const scanSpeed = 0.85;
    const speed = state === "scanning" ? scanSpeed : idleSpeed;
    group.rotation.y += dt * speed;

    if (state !== "result") {
      apple.rotation.y -= dt * 0.15;
      banana.rotation.y += dt * 0.2;
    }

    // lerp opacities/colours toward targets
    apple.material.opacity += (targetOpacity.apple - apple.material.opacity) * 0.08;
    banana.material.opacity += (targetOpacity.banana - banana.material.opacity) * 0.08;
    sweep.material.opacity += (targetOpacity.sweep - sweep.material.opacity) * 0.12;
    apple.material.color.lerp(targetColor.apple, 0.06);
    banana.material.color.lerp(targetColor.banana, 0.06);
    apple.children.forEach((c) => {
      c.material.opacity = apple.material.opacity;
      c.material.color.copy(apple.material.color);
    });
    apple.position.x += (targetX.apple - apple.position.x) * 0.06;
    banana.position.x += (targetX.banana - banana.position.x) * 0.06;

    if (state === "scanning") {
      sweepY += dt * 1.4;
      if (sweepY > 1.3) sweepY = -1.3;
      sweep.position.y = sweepY;
    }

    renderer.render(scene, camera);
  }

  animate();

  return { setState };
}
