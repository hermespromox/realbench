"use client";

import { useEffect, useMemo, useState } from "react";
import { resultKey } from "@/lib/catalog";
import type { VoteCounts } from "@/lib/votes";
import styles from "./vote.module.css";

type Props = {
  scenario: string;
  model: string;
  compact?: boolean;
};

const empty: VoteCounts = { up: 0, down: 0, score: 0, total: 0, percentUpvoted: null };

export default function VoteControl({ scenario, model, compact }: Props) {
  const key = useMemo(() => resultKey(scenario, model), [scenario, model]);
  const [counts, setCounts] = useState<VoteCounts>(empty);
  const [choice, setChoice] = useState<"up" | "down" | "clear">(() => {
    if (typeof window === "undefined") return "clear";
    const stored = window.localStorage.getItem(`realbench-vote:${key}`);
    return stored === "up" || stored === "down" ? stored : "clear";
  });

  useEffect(() => {
    let cancelled = false;
    fetch("/api/votes")
      .then((r) => r.json())
      .then((payload) => {
        if (!cancelled && payload?.votes?.[key]) setCounts(payload.votes[key]);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [key]);

  async function vote(direction: "up" | "down") {
    const next = choice === direction ? "clear" : direction;
    const response = await fetch("/api/votes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario, model, direction: next }),
    });
    const payload = await response.json();
    if (payload?.counts) setCounts(payload.counts);
    setChoice(next);
    if (next === "clear") window.localStorage.removeItem(`realbench-vote:${key}`);
    else window.localStorage.setItem(`realbench-vote:${key}`, next);
  }

  const percent = counts.percentUpvoted == null ? "—" : `${counts.percentUpvoted}%`;

  return (
    <div className={`${styles.wrap} ${compact ? styles.compact : ""}`}>
      <button
        className={`${styles.arrow} ${choice === "up" ? styles.activeUp : ""}`}
        onClick={() => vote("up")}
        aria-pressed={choice === "up"}
        aria-label={`Upvote ${model} on ${scenario}`}
        type="button"
      >
        ▲
      </button>
      <div className={styles.score} title={`${counts.up} up · ${counts.down} down`}>
        <strong>{counts.score}</strong>
        <span>{percent} upvoted</span>
      </div>
      <button
        className={`${styles.arrow} ${choice === "down" ? styles.activeDown : ""}`}
        onClick={() => vote("down")}
        aria-pressed={choice === "down"}
        aria-label={`Downvote ${model} on ${scenario}`}
        type="button"
      >
        ▼
      </button>
    </div>
  );
}
