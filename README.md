# BenchViz

A transparent, one-shot benchmark for frontend animation capability.
Live: https://www.benchviz.com

## Methodology

- Identical prompt per challenge
- One generation per model
- No repairs, retries, or human edits
- One self-contained HTML file
- HTML, CSS, SVG, Canvas, and vanilla JavaScript only
- No external libraries or assets
- Passive animations running at least 15 seconds

## Run 001

Models:
- `x-ai/grok-4.6`
- `openai/gpt-5.6-luna`
- `google/gemini-3.8-flash`
- `z-ai/glm-5.3-flash`
- `tencent/hy4-preview`
- `deepseek/deepseek-v4-flash-0731`
- `moonshotai/kimi-k3`
- `openai/gpt-5.6-sol`
- `meta/muse-spark-1.3`
- `google/gemma-4-31b-it`

Challenges:
1. Solar System — geometry and depth
2. City Traffic — complexity and multi-agent motion
3. Living Aquarium — organic motion
4. Rube Goldberg — visual causality
5. Future Factory — systems coordination
6. Super Mario Bros — autonomous 8-bit platforming
7. Matrix Screen — digital rain / density

## Development

```bash
npm install
npm run dev
```

Regenerate benchmark outputs (requires `OPENROUTER_API_KEY`):

```bash
python3 scripts/generate_benchmark.py
```
