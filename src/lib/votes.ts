import { get, put } from "@vercel/blob";
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

function blobToken() {
  return process.env.BLOB_READ_WRITE_TOKEN || process.env.realbench_READ_WRITE_TOKEN;
}

function memorySlot() {
  return globalThis as typeof globalThis & { __realbenchVotes?: VoteStore };
}

function memoryStore(): VoteStore {
  const slot = memorySlot();
  if (!slot.__realbenchVotes) slot.__realbenchVotes = emptyStore();
  return slot.__realbenchVotes;
}

export function voterFingerprint(ip: string | null, userAgent: string | null) {
  return createHash("sha256")
    .update(`${ip || "unknown"}|${userAgent || "unknown"}`)
    .digest("hex")
    .slice(0, 32);
}

async function readFromBlob(): Promise<VoteStore | null> {
  const token = blobToken();
  if (!token) return null;
  const result = await get(BLOB_PATH, {
    access: "private",
    token,
    useCache: false,
  });
  if (!result || result.statusCode !== 200 || !result.stream) return null;
  const text = await new Response(result.stream).text();
  return JSON.parse(text) as VoteStore;
}

async function writeToBlob(store: VoteStore) {
  const token = blobToken();
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

function mergeStore(fromBlob: VoteStore): VoteStore {
  const base = emptyStore();
  return {
    updatedAt: fromBlob.updatedAt,
    votes: { ...base.votes, ...fromBlob.votes },
    fingerprints: fromBlob.fingerprints || {},
  };
}

export async function loadVotes(): Promise<VoteStore> {
  try {
    const fromBlob = await readFromBlob();
    if (fromBlob) {
      const merged = mergeStore(fromBlob);
      memorySlot().__realbenchVotes = merged;
      return merged;
    }
  } catch {
    // Fall through to process memory, then empty store.
  }
  return memoryStore();
}

export async function saveVotes(store: VoteStore) {
  store.updatedAt = new Date().toISOString();
  memorySlot().__realbenchVotes = store;
  const token = blobToken();
  if (!token) return;
  const persisted = await writeToBlob(store);
  if (!persisted) {
    throw new Error("Vote store was not written to Vercel Blob");
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
