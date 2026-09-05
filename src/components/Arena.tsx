"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { data, modelOrder, resultsForScenario, scenarioOrder, type ScenarioKey } from "@/lib/catalog";
import VoteControl from "./VoteControl";
import styles from "./arena.module.css";

export default function Arena() {
  const [scenario, setScenario] = useState<ScenarioKey>(scenarioOrder[0]);
  const [runKey, setRunKey] = useState(0);
  const [showPrompt, setShowPrompt] = useState(false);
  const selected = data.scenarios[scenario];
  const results = useMemo(() => resultsForScenario(scenario), [scenario]);

  return (
    <section id="arena" className={styles.section}>
      <div className={styles.head}>
        <div>
          <p className={styles.kicker}>Visual arena</p>
          <h2>Compare one-shot builds by use case</h2>
        </div>
        <button className={styles.ghost} type="button" onClick={() => setRunKey((n) => n + 1)}>
          Restart all
        </button>
      </div>

      <div className={styles.tabs} role="tablist" aria-label="Benchmark challenges">
        {scenarioOrder.map((key) => {
          const item = data.scenarios[key];
          return (
            <button
              key={key}
              role="tab"
              type="button"
              aria-selected={scenario === key}
              className={scenario === key ? styles.active : ""}
              onClick={() => setScenario(key)}
            >
              <b>{item.name}</b>
              <small>{item.capability}</small>
            </button>
          );
        })}
      </div>

      <div className={styles.prompt}>
        <div>
          <span>Prompt</span>
          <p>{selected.prompt}</p>
        </div>
        <div className={styles.promptActions}>
          <button type="button" onClick={() => setShowPrompt((v) => !v)}>
            {showPrompt ? "Hide full prompt" : "Read full prompt"}
          </button>
          <Link href={`/challenges/${scenario}`}>Open challenge page</Link>
        </div>
      </div>
      {showPrompt && <pre className={styles.full}>{selected.prompt}</pre>}

      <div className={styles.grid}>
        {results.map((result, index) => {
          const modelKey = modelOrder[index];
          const model = data.models[modelKey];
          return (
            <article className={styles.card} key={`${modelKey}-${runKey}`}>
              <header>
                <div>
                  <h3>{model.name}</h3>
                  <p>{model.vendor}</p>
                </div>
                <VoteControl scenario={scenario} model={modelKey} />
              </header>
              <iframe
                src={`${result.path}?run=${runKey}`}
                title={`${selected.name} by ${model.name}`}
                sandbox="allow-scripts"
                loading="lazy"
              />
              <footer>
                <span>{(result.metrics.bytes / 1024).toFixed(1)} KB</span>
                <span>{result.status}</span>
                <Link href={`/models/${modelKey}`}>Model library</Link>
                <a href={result.path} target="_blank" rel="noreferrer">Open artifact</a>
              </footer>
            </article>
          );
        })}
      </div>
    </section>
  );
}
