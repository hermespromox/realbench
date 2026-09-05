import type { MetadataRoute } from "next";
import { modelOrder, scenarioOrder, SITE_URL } from "@/lib/catalog";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const pages = [
    "",
    "/library",
    ...scenarioOrder.map((slug) => `/challenges/${slug}`),
    ...modelOrder.map((slug) => `/models/${slug}`),
  ];
  return pages.map((path) => ({
    url: `${SITE_URL}${path || "/"}`,
    lastModified: now,
    changeFrequency: path === "" ? "daily" : "weekly",
    priority: path === "" ? 1 : path === "/library" ? 0.9 : 0.8,
  }));
}
