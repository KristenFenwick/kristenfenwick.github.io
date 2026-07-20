# Particle Storm

Interactive hand-tracking particle sphere that runs in the browser.

**Live demo:** [kristenfenwick.github.io/particle-storm](https://kristenfenwick.github.io/particle-storm/)

## What it does

- Tracks your hands with the webcam (MediaPipe Hands)
- Builds a ~3,000-particle glowing sphere (Three.js)
- **Pinch** to charge · **release** to explode · particles reform with a wave
- Two hands: change distance to scale the sphere
- Optional audio feedback

## Controls

| Gesture / button | Action |
|------------------|--------|
| Show hand | Start tracking |
| Pinch (thumb + index) | Charge |
| Release pinch | Explode particles |
| Two hands apart/together | Scale sphere |
| **Camera** | Toggle webcam preview |
| **Audio** | Toggle sound |
| **Reset** | Rebuild the sphere |

## Camera permissions

The camera API only works on a **secure context**:

- `https://…` (this GitHub Pages deploy) — works
- `http://localhost` — works
- Opening `index.html` as a local `file://` page — often blocked

When the page loads, allow camera access in the browser prompt. Chrome / Edge / Firefox are recommended.

## Run locally

```bash
cd particle-storm
python3 -m http.server 8765
```

Open [http://localhost:8765](http://localhost:8765) and allow the camera.

## Stack

- Vanilla HTML / CSS / JavaScript
- [Three.js](https://threejs.org/) (particles)
- [MediaPipe Hands](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker) (CDN)

No build step. One file: `index.html`.

## License

Personal project — use and remix freely with credit appreciated.
