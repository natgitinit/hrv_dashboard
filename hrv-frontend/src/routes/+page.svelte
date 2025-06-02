<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import * as d3 from 'd3';

  let rr = 60;
  let displayRR = 60;
  let svgContainer: SVGSVGElement;
  let lastBeatTime = Date.now();
  const width = 1000;
  const height = 400;
  const n = 50; // Number of points per layer
  let layers = 8;
  let data: number[][] = [];
  let offset = 0; // For shifting waves like a heart rate monitor

  // 🎨 Multiple color palettes based on RR zone
  const colorPalettes: string[][] = [
    // RR <= 60 → calm blues
    ['#00F0FF', '#00FFC6', '#18FFFF', '#3D5AFE', '#2979FF', '#00B0FF', '#1DE9B6', '#64FFDA', '#00E5FF', '#80D8FF'],
    // 61–75 → fresh greens
    ['#00E676', '#76FF03', '#C6FF00', '#B2FF59', '#69F0AE', '#00C853', '#AEEA00', '#76FF03', '#64DD17', '#00E676'],
    // 76–90 → purples & pinks
    ['#D500F9', '#651FFF', '#9C27B0', '#E040FB', '#BA68C8', '#F48FB1', '#CE93D8', '#D1C4E9', '#F06292', '#E91E63'],
    // 91–100 → orange & hot pink
    ['#FF1744', '#F50057', '#FF4081', '#FF5722', '#FF7043', '#FF8A65', '#FFAB91', '#FF5252', '#FF6E40', '#FF3D00'],
    // >100 → intense reds
    ['#FF0000', '#FF1744', '#FF6D00', '#FF3D00', '#F44336', '#EF5350', '#E53935', '#D32F2F', '#C62828', '#B71C1C']
  ];

  function getPalette(rr: number): string[] {
    if (rr <= 60) return colorPalettes[0];
    if (rr <= 75) return colorPalettes[1];
    if (rr <= 90) return colorPalettes[2];
    if (rr <= 100) return colorPalettes[3];
    return colorPalettes[4];
  }

  // Pulse speed matches heartbeat (e.g., 60 BPM = 1s per beat)
  $: pulseSpeed = rr > 0 ? 60 / rr : 1;

  // 💥 Create bump data for waves
  function bump(a: number[], n: number) {
    const x = 1 / (0.1 + Math.random());
    const y = 2 * Math.random() - 0.5;
    const z = 10 / (0.1 + Math.random());
    for (let i = 0; i < n; ++i) {
      const w = (i / n - y) * z;
      a[i] += x * Math.exp(-w * w);
    }
  }

  function bumps(n: number, m: number) {
    const a = Array.from({ length: n }, () => 0);
    for (let i = 0; i < m; ++i) bump(a, n);
    return a;
  }

  // Define scales and elements globally so animate can access them
  let x: d3.ScaleLinear<number, number>;
  let y: d3.ScaleLinear<number, number>;
  let area: d3.Area<[number, number]>;
  let line: d3.Line<[number, number]>;
  let paths: d3.Selection<SVGPathElement, d3.Series<number[], number>, SVGSVGElement, unknown>;
  let pulseLine: d3.Selection<SVGPathElement, d3.Series<number[], number>, SVGSVGElement, unknown>;
  let stack: d3.Stack<any, number[], number>;
  let lastTime = performance.now();

  function transpose(array: number[][]): number[][] {
    return array[0].map((_, colIndex) => array.map(row => row[colIndex]));
  }

  function drawWaves() {
  const svg = d3.select(svgContainer)
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("preserveAspectRatio", "xMidYMid meet");

    svg.selectAll("*").remove();

    stack = d3.stack().keys(d3.range(layers)).offset(d3.stackOffsetWiggle);
    const shiftedData = data.map(layer => layer.map((_, i) => layer[(i + Math.floor(offset)) % n]));
    const stackedData = stack(transpose(shiftedData));

    x = d3.scaleLinear().domain([0, n - 1]).range([0, width]);
    const minY = d3.min(stackedData.flat(2)) ?? 0; // Fallback to 0 if undefined
    const maxY = d3.max(stackedData.flat(2)) ?? 1; // Fallback to 1 if undefined
    y = d3.scaleLinear()
      .domain([minY, maxY])
      .range([height, 0]);

    area = d3.area<[number, number]>()
      .x((_, i) => x(i))
      .y0(d => y(d[0]))
      .y1(d => y(d[1]))
      .curve(d3.curveCardinal);

    line = d3.line<[number, number]>()
      .x((_, i) => x(i))
      .y(d => y(d[1]))
      .curve(d3.curveCardinal);

    // Initial wave paths
    paths = svg.selectAll(".wave-path")
      .data(stackedData)
      .enter()
      .append("path")
      .attr("class", "wave-path")
      .attr("fill-opacity", 1)
      .attr("d", area)
      .attr("fill", (_, i) => getPalette(displayRR)[i % getPalette(displayRR).length]);

    // Initial pulse line
    pulseLine = svg.append("path")
      .datum(stackedData[stackedData.length - 1])
      .attr("class", "pulse-line")
      .attr("fill", "none")
      .attr("stroke-width", 2)
      .attr("stroke-opacity", 1)
      .attr("filter", "url(#glow)")
      .attr("d", line)
      .attr("stroke", getPalette(displayRR)[0]);

    // Start the animation loop
    requestAnimationFrame(animate);
  }

  function animate(time: number) {
    const delta = (time - lastTime) / 1000;
    if (delta < 1 / 80) {
      requestAnimationFrame(animate);
      return;
    }
    lastTime = time;

    const palette = getPalette(displayRR);
    offset = (offset + 0.01 * delta * (80 / pulseSpeed)) % n; // Keep fractional offset

    // Interpolate wave positions for smoother flow
    const newShiftedData = data.map(layer => {
      return layer.map((_, i) => {
        const index = (i + offset) % n;
        const floorIndex = Math.floor(index);
        const frac = index - floorIndex;
        const nextIndex = (floorIndex + 1) % n;
        // Linearly interpolate between two points
        return layer[floorIndex] * (1 - frac) + layer[nextIndex] * frac;
      });
    });
    const newStackedData = stack(transpose(newShiftedData));

    y.domain([d3.min(newStackedData.flat(2)) || 0, d3.max(newStackedData.flat(2)) || 1]);

    paths.data(newStackedData)
      .attr("d", area)
      .attr("fill", (_, i) => palette[i % palette.length]);

    const phase = (time % (pulseSpeed * 1000)) / (pulseSpeed * 1000);
    const spike = phase < 0.5 ? phase * 0.4 : (1 - phase) * 0.4;
    pulseLine.datum(newStackedData[newStackedData.length - 1])
      .attr("stroke", palette[0])
      .attr("d", d => {
        const scaledData = d.map(point => [point[0], point[1] * (1 + spike)]);
        return line(scaledData);
      });

    // Animate motion blur on pulseLine
    d3.select("#glow .blurValues")
      .transition()
      .duration(pulseSpeed * 1000 / 2)
      .ease(d3.easeCubic)
      .attrTween("stdDeviation", () => d3.interpolateString("0.1 0", "8 0"))
      .transition()
      .duration(pulseSpeed * 1000 / 2)
      .ease(d3.easeCubic)
      .attrTween("stdDeviation", () => d3.interpolateString("8 0", "0.1 0"));

    requestAnimationFrame(animate);
  }

  async function fetchData() {
    try {
      const res = await fetch("http://localhost:8000/latest");
      const result = await res.json();
      if (result.rr !== undefined) {
        rr = result.rr;
        displayRR += (rr - displayRR) * 0.2;

        const bumpCount = Math.floor((displayRR - 40) / 5);
        data = d3.range(layers).map(() => bumps(n, bumpCount));

        // ❤️ Pulse heart icon
        const heartbeat = document.getElementById("heartbeat") as HTMLElement;
        if (heartbeat) {
          const color = getPalette(displayRR)[0];
          heartbeat.style.color = color;
          heartbeat.style.filter = `drop-shadow(0 0 12px ${color})`;
          heartbeat.style.transform = "scale(1.4)";
          setTimeout(() => {
            heartbeat.style.transform = "scale(1)";
          }, 200);
        }

        drawWaves();
      }
    } catch (err) {
      console.error("Fetch error:", err);
    }
  }

  onMount(() => {
    data = Array.from({ length: layers }, () => bumps(n, 45));
    drawWaves();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  });
</script>

<style>
  .container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    background: #1a1a1a;
    color: #fff;
    font-family: Arial, sans-serif;
  }

  .heart-rate {
    font-size: 24px;
    margin-bottom: 20px;
  }

  .svg-container {
    width: 100%;
    max-width: 1000px;
    height: 600px;
  }
</style>

<div class="container">
  <div class="heart-rate">Heart Rate: {Math.round(displayRR)} BPM</div>
  <svg bind:this={svgContainer} class="svg-container">
    <defs>
      <filter id="glow">
        <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="blur"/>
        <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -7" result="glow"/>
        <feMerge>
          <feMergeNode in="glow"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
    </defs>
  </svg>
</div>

<div class="flex flex-col items-center mt-6 space-y-2">
  <h1 class="text-center text-4xl font-extrabold tracking-tight text-purple-900 md:text-5xl lg:text-6xl">
    Heart Rate: {Math.round(displayRR)} BPM
  </h1>

  <svg
    id="heartbeat"
    xmlns="http://www.w3.org/2000/svg"
    class="w-12 h-12 transition-transform duration-200 ease-in-out"
    viewBox="0 0"
    fill="currentColor"
  >
    <path
      d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5
         2 5.42 4.42 3 7.5 3c1.74 0 3.41 0.81 4.5 2.09
         C13.09 3.81 14.76 3 16.5 3
         19.58 3 22 5.42 22 8.5
         c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
    />
  </svg>
</div>