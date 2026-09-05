import type { Metadata } from "next";
import Link from "next/link";
import { data, modelOrder, scenarioOrder } from "@/lib/catalog";
import styles from "../library.module.css";

export const metadata: Metadata = {
  title: "Library",
  description: "Browse BenchViz artifacts by model or by use case. Each card is a one-shot HTML animation.",
  alternates: { canonical: "/library" },
};

export default function LibraryPage() {
  return (
    <main className={styles.page}>
      <p className={styles.kicker}>Library</p>
      <h1>Browse by model and by use case</h1>
      <p className={styles.lead}>
        The arena compares models on one challenge. The library lets you inspect a single model
        across every challenge, or a challenge across every model.
      </p>

      <section>
        <h2>By model</h2>
        <div className={styles.grid}>
          {modelOrder.map((key) => {
            const model = data.models[key];
            return (
              <Link className={styles.card} key={key} href={`/models/${key}`}>
                <small>{model.vendor}</small>
                <h3>{model.name}</h3>
                <p>{scenarioOrder.length} published challenges</p>
              </Link>
            );
          })}
        </div>
      </section>

      <section>
        <h2>By use case</h2>
        <div className={styles.grid}>
          {scenarioOrder.map((key) => {
            const scenario = data.scenarios[key];
            return (
              <Link className={styles.card} key={key} href={`/challenges/${key}`}>
                <small>{scenario.capability}</small>
                <h3>{scenario.name}</h3>
                <p>{modelOrder.length} model builds</p>
              </Link>
            );
          })}
        </div>
      </section>
    </main>
  );
}
