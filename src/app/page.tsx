import Link from "next/link";
import Arena from "@/components/Arena";
import { data, modelOrder, scenarioOrder } from "@/lib/catalog";
import styles from "./home.module.css";

export default function Home() {
  return (
    <main>
      <section className={styles.hero}>
        <p className={styles.kicker}>Run 001 · {modelOrder.length} models · {scenarioOrder.length} challenges</p>
        <h1>See what models can actually build.</h1>
        <p className={styles.lead}>
          Identical prompts. One generation each. No human edits. Browse the live HTML by use case
          or by model, then upvote the strongest artifact.
        </p>
        <div className={styles.actions}>
          <a className={styles.primary} href="#arena">Open visual arena</a>
          <Link className={styles.secondary} href="/library">Browse model library</Link>
        </div>
        <dl className={styles.stats}>
          <div><dt>Frontier models</dt><dd>{modelOrder.length}</dd></div>
          <div><dt>Visual challenges</dt><dd>{scenarioOrder.length}</dd></div>
          <div><dt>Published builds</dt><dd>{data.results.length}</dd></div>
          <div><dt>Human edits</dt><dd>0</dd></div>
        </dl>
      </section>
      <Arena />
      <section id="methodology" className={styles.method}>
        <p className={styles.kicker}>Methodology</p>
        <h2>Transparent, one-shot, comparable.</h2>
        <div className={styles.methodGrid}>
          <article><h3>Identical prompt</h3><p>Every model receives the same task and system constraints.</p></article>
          <article><h3>Published as generated</h3><p>No cherry-picked variants. Infra retries are labeled in the manifest.</p></article>
          <article><h3>Native web only</h3><p>One HTML file. HTML, CSS, SVG, Canvas, and vanilla JavaScript.</p></article>
          <article><h3>Community ranking</h3><p>Reddit-style upvotes compute score and percent upvoted per artifact.</p></article>
        </div>
      </section>
    </main>
  );
}
