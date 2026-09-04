"use client";

import { useEffect, useMemo, useState } from "react";
import data from "@/data/results.json";
import styles from "./page.module.css";

type Result = (typeof data.results)[number];
type ScenarioKey = keyof typeof data.scenarios;
type ModelKey = keyof typeof data.models;

const scenarioOrder = Object.keys(data.scenarios) as ScenarioKey[];
const modelOrder = Object.keys(data.models) as ModelKey[];

function Check({ value }: { value: boolean }) {
  return <span className={value ? styles.pass : styles.fail}>{value ? "PASS" : "FAIL"}</span>;
}

export default function Home() {
  const [scenario, setScenario] = useState<ScenarioKey>(scenarioOrder[0]);
  const [runKey, setRunKey] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [showPrompt, setShowPrompt] = useState(false);

  const selectedScenario = data.scenarios[scenario];
  const selectedResults = useMemo(
    () => modelOrder.map((model) => data.results.find((r) => r.scenario === scenario && r.model === model) as Result),
    [scenario]
  );

  useEffect(() => {
    const timer = window.setInterval(() => setElapsed((n) => n + 1), 1000);
    return () => window.clearInterval(timer);
  }, [runKey, scenario]);

  function restartAll() {
    setElapsed(0);
    setRunKey((n) => n + 1);
  }

  function selectScenario(key: ScenarioKey) {
    setElapsed(0);
    setScenario(key);
  }

  return (
    <main>
      <nav className={styles.nav}>
        <a className={styles.brand} href="#top" aria-label="RealBench home">
          <span className={styles.mark}>R</span>
          <span>RealBench</span>
          <span className={styles.beta}>BETA</span>
        </a>
        <div className={styles.navMeta}>
          <span><i className={styles.liveDot} /> Live benchmark</span>
          <a href="#methodology">Methodology</a>
          <a href="https://github.com/hermespromox/realbench" target="_blank" rel="noreferrer">GitHub ↗</a>
        </div>
      </nav>

      <section id="top" className={styles.hero}>
        <div className={styles.eyebrow}>FRONTEND CAPABILITY EVALUATION / RUN 001</div>
        <h1>See what models<br />can actually build.</h1>
        <p className={styles.lead}>
          Same prompt. One generation per published artifact. Fifteen seconds of autonomous animation,
          rendered side by side in your browser.
        </p>
        <div className={styles.heroStats}>
          <div><strong>{modelOrder.length}</strong><span>Frontier models</span></div>
          <div><strong>{scenarioOrder.length}</strong><span>Visual challenges</span></div>
          <div><strong>{data.results.length}</strong><span>Published builds</span></div>
          <div><strong>0</strong><span>Human edits</span></div>
        </div>
      </section>

      <section className={styles.benchSection}>
        <div className={styles.sectionTop}>
          <div>
            <span className={styles.sectionIndex}>01</span>
            <h2>Visual arena</h2>
          </div>
          <div className={styles.runControls}>
            <span className={styles.timer}><i /> {String(Math.floor(elapsed / 60)).padStart(2, "0")}:{String(elapsed % 60).padStart(2, "0")}</span>
            <button onClick={restartAll}>↻ Restart all</button>
          </div>
        </div>

        <div className={styles.scenarioTabs} role="tablist" aria-label="Benchmark scenarios">
          {scenarioOrder.map((key, index) => {
            const item = data.scenarios[key];
            return (
              <button
                role="tab"
                aria-selected={scenario === key}
                className={scenario === key ? styles.activeTab : ""}
                key={key}
                onClick={() => selectScenario(key)}
              >
                <span className={styles.tabNumber}>0{index + 1}</span>
                <span className={styles.tabIcon}>{item.icon}</span>
                <span><b>{item.name}</b><small>{item.capability}</small></span>
              </button>
            );
          })}
        </div>

        <div className={styles.promptBar}>
          <div><span>PROMPT</span><p>{selectedScenario.prompt}</p></div>
          <button onClick={() => setShowPrompt((v) => !v)}>{showPrompt ? "Collapse" : "Read full prompt"}</button>
        </div>
        {showPrompt && <pre className={styles.fullPrompt}>{selectedScenario.prompt}</pre>}

        <div className={styles.modelGrid}>
          {selectedResults.map((result, index) => {
            const modelKey = modelOrder[index];
            const model = data.models[modelKey];
            return (
              <article className={styles.modelCard} key={`${modelKey}-${runKey}`}>
                <header>
                  <div>
                    <span className={styles.rank}>0{index + 1}</span>
                    <div><h3>{model.name}</h3><p>{model.vendor}</p></div>
                  </div>
                  <span className={result.status === "ok" ? styles.ready : styles.error}>{result.status}</span>
                </header>
                <div className={styles.frameWrap}>
                  <iframe
                    src={`${result.path}?run=${runKey}`}
                    title={`${selectedScenario.name} by ${model.name}`}
                    sandbox="allow-scripts"
                    loading="eager"
                  />
                  <span className={styles.frameLabel}>LIVE HTML</span>
                </div>
                <footer>
                  <span>{(result.metrics.bytes / 1024).toFixed(1)} KB</span>
                  <span>{result.metrics.dom_nodes_approx} nodes</span>
                  <span>{result.duration_seconds.toFixed(1)}s generation</span>
                  <a href={result.path} target="_blank" rel="noreferrer">Open ↗</a>
                </footer>
              </article>
            );
          })}
        </div>
      </section>

      <section className={styles.metricsSection}>
        <div className={styles.sectionTop}>
          <div><span className={styles.sectionIndex}>02</span><h2>Technical signals</h2></div>
          <p>Deterministic checks only. Visual quality is yours to judge.</p>
        </div>
        <div className={styles.metricsTable}>
          <div className={styles.metricsHead}><span>Model</span><span>Valid HTML</span><span>Self-contained</span><span>JS parses</span><span>Canvas / SVG</span><span>Output</span></div>
          {selectedResults.map((result, index) => {
            const model = data.models[modelOrder[index]];
            return <div className={styles.metricsRow} key={result.model}>
              <strong>{model.name}</strong>
              <Check value={result.metrics.valid_html} />
              <Check value={result.metrics.self_contained} />
              <Check value={result.metrics.js_parses} />
              <span>{result.metrics.uses_canvas ? "Canvas" : "—"}{result.metrics.uses_svg ? `${result.metrics.uses_canvas ? " + " : ""}SVG` : ""}</span>
              <span>{result.metrics.bytes.toLocaleString()} bytes</span>
            </div>;
          })}
        </div>
      </section>

      <section id="methodology" className={styles.methodSection}>
        <div className={styles.sectionTop}><div><span className={styles.sectionIndex}>03</span><h2>Methodology</h2></div></div>
        <div className={styles.methodGrid}>
          <article><span>01</span><h3>Identical prompt</h3><p>Every model receives the exact same task and system constraints.</p></article>
          <article><span>02</span><h3>Transparent generation</h3><p>No cherry-picked variants. Any token-limit rerun is preserved and labeled in the benchmark manifest.</p></article>
          <article><span>03</span><h3>Native web only</h3><p>One HTML file. Vanilla HTML, CSS, SVG, Canvas, and JavaScript.</p></article>
          <article><span>04</span><h3>Passive evaluation</h3><p>No clicks required. Every scene runs autonomously for visual comparison.</p></article>
        </div>
        <div className={styles.ruleLine}>
          <span>15 SEC MINIMUM</span><span>NO EXTERNAL ASSETS</span><span>NO LIBRARIES</span><span>NO HUMAN EDITS</span>
        </div>
      </section>

      <footer className={styles.siteFooter}>
        <div className={styles.brand}><span className={styles.mark}>R</span><span>RealBench</span></div>
        <p>Frontend capability, rendered honestly.</p>
        <span>RUN 001 · {new Date(data.generated_at).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })}</span>
      </footer>
    </main>
  );
}
