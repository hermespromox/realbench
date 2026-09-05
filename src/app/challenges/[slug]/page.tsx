import type { Metadata } from "next";
import { notFound } from "next/navigation";
import ArtifactGallery from "@/components/ArtifactGallery";
import { data, modelOrder, resultsForScenario, scenarioOrder, type ScenarioKey } from "@/lib/catalog";
import styles from "../../library.module.css";

type Props = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return scenarioOrder.map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const scenario = data.scenarios[slug as ScenarioKey];
  if (!scenario) return {};
  const title = `${scenario.name} challenge`;
  const description = `Compare ${modelOrder.length} one-shot HTML builds for the RealBench ${scenario.name} challenge: ${scenario.capability}.`;
  return {
    title,
    description,
    alternates: { canonical: `/challenges/${slug}` },
    openGraph: { title, description, url: `/challenges/${slug}` },
  };
}

export default async function ChallengePage({ params }: Props) {
  const { slug } = await params;
  const scenario = data.scenarios[slug as ScenarioKey];
  if (!scenario) notFound();
  const results = resultsForScenario(slug as ScenarioKey);

  return (
    <main className={styles.page}>
      <p className={styles.kicker}>Use case</p>
      <h1>{scenario.name}</h1>
      <p className={styles.lead}>{scenario.capability}. {scenario.prompt}</p>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            name: `${scenario.name} · RealBench`,
            description: scenario.prompt,
          }),
        }}
      />
      <ArtifactGallery
        results={results}
        hrefFor={(result) => ({ label: data.models[result.model as keyof typeof data.models].name, href: `/models/${result.model}` })}
      />
    </main>
  );
}
