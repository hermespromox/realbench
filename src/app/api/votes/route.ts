import { NextRequest, NextResponse } from "next/server";
import { resultKey } from "@/lib/catalog";
import { applyVote, isKnownResult, loadVotes, publicVotes, saveVotes, voterFingerprint, type VoteDirection } from "@/lib/votes";

export const dynamic = "force-dynamic";

function clientIp(request: NextRequest) {
  return request.headers.get("x-forwarded-for")?.split(",")[0]?.trim()
    || request.headers.get("x-real-ip")
    || "unknown";
}

export async function GET() {
  const store = await loadVotes();
  return NextResponse.json({ votes: publicVotes(store), updatedAt: store.updatedAt });
}

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => null) as {
    scenario?: string;
    model?: string;
    direction?: VoteDirection;
  } | null;

  const scenario = body?.scenario || "";
  const model = body?.model || "";
  const direction = body?.direction;
  if (!isKnownResult(scenario, model) || !["up", "down", "clear"].includes(String(direction))) {
    return NextResponse.json({ error: "Invalid vote" }, { status: 400 });
  }

  const store = await loadVotes();
  const key = resultKey(scenario, model);
  const fingerprint = voterFingerprint(clientIp(request), request.headers.get("user-agent"));
  const counts = applyVote(store, key, fingerprint, direction as VoteDirection);
  await saveVotes(store);

  return NextResponse.json({
    key,
    direction,
    counts,
    votes: publicVotes(store),
  });
}
