import Link from "next/link";
import VoteControl from "@/components/VoteControl";
import { data, type Result } from "@/lib/catalog";
import styles from "./gallery.module.css";

export default function ArtifactGallery({
  results,
  hrefFor,
}: {
  results: Result[];
  hrefFor: (result: Result) => { label: string; href: string };
}) {
  return (
    <div className={styles.grid}>
      {results.map((result) => {
        const model = data.models[result.model as keyof typeof data.models];
        const scenario = data.scenarios[result.scenario as keyof typeof data.scenarios];
        const link = hrefFor(result);
        return (
          <article className={styles.card} key={`${result.scenario}-${result.model}`}>
            <header>
              <div>
                <h3>{model.name}</h3>
                <p>{scenario.name} · {model.vendor}</p>
              </div>
              <VoteControl scenario={result.scenario} model={result.model} compact />
            </header>
            <iframe src={result.path} title={`${scenario.name} by ${model.name}`} sandbox="allow-scripts" loading="lazy" />
            <footer>
              <span>{(result.metrics.bytes / 1024).toFixed(1)} KB</span>
              <Link href={link.href}>{link.label}</Link>
              <a href={result.path} target="_blank" rel="noreferrer">Open artifact</a>
            </footer>
          </article>
        );
      })}
    </div>
  );
}
