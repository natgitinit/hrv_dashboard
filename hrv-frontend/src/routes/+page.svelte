<!-- <script lang="ts">
  import {
    Chart,
    Svg,
    Group,
    Circle,
    ForceSimulation,
  } from 'layerchart';

  import {
    forceX,
    forceY,
    forceManyBody,
    forceCollide,
    type SimulationNodeDatum,
    type Simulation,
  } from 'd3-force';

  import { onMount } from 'svelte';

  // 🎨 Color palette
  function groupColor(group: number) {
    const colors = ['#00BCD4', '#4CAF50', '#FFC107', '#E91E63'];
    return colors[group % colors.length];
  }

  // 🧠 Node data with radius and position
  let nodes: (SimulationNodeDatum & {
    id: number;
    group: number;
    r: number;
    x: number;
    y: number;
  })[] = Array.from({ length: 7 }, (_, i) => ({
    id: i,
    group: 1,
    r: i === 0 ? 10 : 10 + Math.random() * 5,
    x: 400,
    y: 400,
  }));

  // 🫀 RR state
  let rr = 60;
  let displayRR = rr;

  // 📦 D3 simulation instance
  let simulation: Simulation<SimulationNodeDatum>;

  // 🔁 Fetch RR and update sim
  async function fetchData() {
  try {
    const res = await fetch('http://localhost:8000/latest');
    const data = await res.json();
    console.log('📡 Data', data);
    if (data.rr !== undefined) {
      rr = data.rr;
      displayRR += (rr - displayRR) * 0.1;

      // Wait for simulation to be bound and valid
      if (simulation?.force && typeof simulation.force === 'function') {
        const chargeForce = simulation.force('charge');
        if (chargeForce && typeof chargeForce.strength === 'function') {
          chargeForce.strength((d, i) =>
            i === 0 ? (-400 * 2) / 3 : (displayRR - 60) * 3
          );
          simulation.alpha(0.5).restart();
        }
      }
    }
  } catch (err) {
    console.error('Fetch error:', err);
  }
}


  onMount(() => {
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  });
</script> -->


<!-- <div class="h-[800px] bg-white p-4 border border-gray-300 rounded shadow overflow-hidden">
  <Chart data={nodes} let:width let:height>
    <Svg width={width} height={height} class="bg-sky-100 border border-blue-400">
      <ForceSimulation
      bind:this={simulation}
        forces={{
          x: forceX(() => width / 2).strength(0.05),
          y: forceY(() => height / 2).strength(0.05),
          collide: forceCollide<SimulationNodeDatum & { r: number }>()
            .radius(d => d.r + 1)
            .iterations(3),
            charge: forceManyBody().strength((d, i) =>
              i === 0 ? (-width * 2) / 3 : (displayRR - 60) * 3
            ),
        }}
        alphaTarget={0.3}
        velocityDecay={0.1}
        let:nodes
      >
        <Group center>
          {#each nodes as node, i}
            <Circle
              cx={node.x ?? 200}
              cy={node.y ?? 200}
              r={node.r}
              fill={groupColor(node.group)}
              opacity="0.8"
            />
          {/each}
        </Group>

        <rect
          {width}
          {height}
          on:pointermove={(e) => {
            nodes[0].fx = e.offsetX - width / 2;
            nodes[0].fy = e.offsetY - height / 2;
          }}
          class="fill-transparent"
        />
      </ForceSimulation>
    </Svg>
  </Chart>
</div> -->


<script lang="ts">
  import { onMount } from 'svelte';
  import * as d3 from 'd3';

  let rr = 60;
  let displayRR = 60;
  let svgContainer: SVGSVGElement;

  const width = 1000;
  const height = 400;
  const n = 100; // number of points per layer
  let layers = 10;
  let data: number[][] = [];

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

  // 💥 Create bump data
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

  function drawWaves() {
    const svg = d3.select(svgContainer)
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("preserveAspectRatio", "xMidYMid meet");

    svg.selectAll("*").remove();

    const stack = d3.stack().keys(d3.range(layers)).offset(d3.stackOffsetWiggle);
    const stackedData = stack(d3.transpose(data));

    const x = d3.scaleLinear().domain([0, n - 1]).range([0, width]);
    const y = d3.scaleLinear()
      .domain([d3.min(stackedData.flat(2)) || 0, d3.max(stackedData.flat(2)) || 1])
      .range([height, 0]);

    const area = d3.area<[number, number]>()
      .x((_, i) => x(i))
      .y0(d => y(d[0]))
      .y1(d => y(d[1]))
      .curve(d3.curveCardinal);

    const palette = getPalette(displayRR);

    svg.selectAll("path")
      .data(stackedData)
      .join("path")
      .attr("fill", (_, i) => palette[i % palette.length])
      .attr("opacity", 0.88)
      .attr("d", area);
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
        drawWaves();

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
      }
    } catch (err) {
      console.error("Fetch error:", err);
    }
  }

  onMount(() => {
    data = Array.from({ length: layers }, () => bumps(n, 5));
    drawWaves();
    const interval = setInterval(fetchData, 1500);
    return () => clearInterval(interval);
  });
</script>



<div class="p-4 bg-white rounded shadow w-full max-w-5xl mx-auto">
  <svg bind:this={svgContainer} class="w-full h-[300px]"></svg>
</div>

<div class="flex flex-col items-center mt-6 space-y-2">
  <h1 class="text-center text-4xl font-extrabold tracking-tight text-purple-900 md:text-5xl lg:text-6xl">
    RR: {Math.round(displayRR)} ms
  </h1>

  <svg
    id="heartbeat"
    xmlns="http://www.w3.org/2000/svg"
    class="w-12 h-12 transition-transform duration-200 ease-in-out"
    viewBox="0 0  120"
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
