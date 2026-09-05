import { put } from "@vercel/blob";
import { createHash } from "crypto";
import { modelOrder, resultKey, scenarioOrder } from "./catalog";

export type VoteDirection = "up" | "down" | "clear";

export type VoteCounts = {
  up: number;
  down: number;
  score: number;
  total: number;
  percentUpvoted: number | null;
};

export type VoteStore = {
  updatedAt: string;
  votes: Record<string, VoteCounts>;
  fingerprints: Record<string, VoteDirection>;
};

const BLOB_PATH = "realbench-votes.json";

function emptyCounts(): VoteCounts {
  return { up: 0, down: 0, score: 0, total: 0, percentUpvoted: null };
}

function finalize(counts: VoteCounts): VoteCounts {
  const total = counts.up + counts.down;
  return {
    up: counts.up,
    down: counts.down,
    score: counts.up - counts.down,
    total,
    percentUpvoted: total === 0 ? null : Math.round((counts.up / total) * 100),
  };
}

function emptyStore(): VoteStore {
  const votes: Record<string, VoteCounts> = {};
  for (const scenario of scenarioOrder) {
    for (const model of modelOrder) {
      votes[resultKey(scenario, model)] = emptyCounts();
    }
  }
  return { updatedAt: new Date().toISOString(), votes, fingerprints: {} };
}

function blobUrl() {
  const base = process.env.BLOB_BASE_URL || process.env.realbench_BASE_URL;
  if (base) return `${base.replace(/\/$/, "")}/${BLOB_PATH}`;
  return `https://blob.vercel-storage.com/${BLOB_PATH}`;
}

export function voterFingerprint(ip: string | null, userAgent: string | null) {
  return createHash("sha256")
    .update(`${ip || "unknown"}|${userAgent || "unknown"}`)
    .digest("hex")
    .slice(0, 32);
}

async function readFromBlob(): Promise<VoteStore | null> {
  if (!process.env.BLOB_READ_WRITE_TOKEN && !process.env.realbench_READ_WRITE_TOKEN) return null;
  const response = await fetch(blobUrl(), { cache: "no-store" });
  if (!response.ok) return null;
  return (await response.json()) as VoteStore;
}

async function writeToBlob(store: VoteStore) {
  const token = process.env.BLOB_READ_WRITE_TOKEN || process.env.realbench_READ_WRITE_TOKEN;
  if (!token) return false;
  await put(BLOB_PATH, JSON.stringify(store), {
    access: "private",
    addRandomSuffix: false,
    allowOverwrite: true,
    contentType: "application/json",
    token,
  });
  return true;
}

function memoryStore(): VoteStore {
  const globalStore = globalThis as typeof globalThis & { __realbenchVotes?: VoteStore };
  if (!globalStore.__realbenchVotes) globalStore.__realbenchVotes = emptyStore();
  return globalStore.__realbenchVotes;
}

export async function loadVotes(): Promise<VoteStore> {
  try {
    const fromBlob = await readFromBlob();
    if (fromBlob) {
      const base = emptyStore();
      return {
        updatedAt: fromBlob.updatedAt,
        votes: { ...base.votes, ...fromBlob.votes },
        fingerprints: fromBlob.fingerprints || {},
      };
    }
  } catch {
    // Fall through.
  }
  return memoryStore();
}

export async function saveVotes(store: VoteStore) {
  store.updatedAt = new Date().toISOString();
  const persisted = await writeToBlob(store).catch(() => false);
  if (!persisted) {
    const globalStore = globalThis as typeof globalThis & { __realbenchVotes?: VoteStore };
    globalStore.__realbenchVotes = store;
  }
}

export function publicVotes(store: VoteStore) {
  const votes: Record<string, VoteCounts> = {};
  for (const [key, value] of Object.entries(store.votes)) {
    votes[key] = finalize(value);
  }
  return votes;
}

export function applyVote(store: VoteStore, key: string, fingerprint: string, direction: VoteDirection) {
  const current = finalize(store.votes[key] || emptyCounts());
  const previous = store.fingerprints[`${key}:${fingerprint}`] || "clear";
  let up = current.up;
  let down = current.down;
  if (previous === "up") up = Math.max(0, up - 1);
  if (previous === "down") down = Math.max(0, down - 1);
  if (direction === "up") up += 1;
  if (direction === "down") down += 1;
  store.votes[key] = finalize({ up, down, score: 0, total: 0, percentUpvoted: null });
  const fingerprintKey = `${key}:${fingerprint}`;
  if (direction === "clear") delete store.fingerprints[fingerprintKey];
  else store.fingerprints[fingerprintKey] = direction;
  return store.votes[key];
}

export function isKnownResult(scenario: string, model: string) {
  return scenarioOrder.includes(scenario as (typeof scenarioOrder)[number])
    && modelOrder.includes(model as (typeof modelOrder)[number]);
}
