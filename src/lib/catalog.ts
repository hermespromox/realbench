import data from "@/data/results.json";

export const SITE_URL = "https://realbench-delta.vercel.app";
export const SITE_NAME = "RealBench";

export type Result = (typeof data.results)[number];
export type ScenarioKey = keyof typeof data.scenarios;
export type ModelKey = keyof typeof data.models;

export const scenarioOrder = Object.keys(data.scenarios) as ScenarioKey[];
export const modelOrder = Object.keys(data.models) as ModelKey[];

export function resultKey(scenario: string, model: string) {
  return `${scenario}::${model}`;
}

export function findResult(scenario: string, model: string) {
  return data.results.find((item) => item.scenario === scenario && item.model === model);
}

export function resultsForScenario(scenario: ScenarioKey) {
  return modelOrder.map((model) => findResult(scenario, model)).filter(Boolean) as Result[];
}

export function resultsForModel(model: ModelKey) {
  return scenarioOrder.map((scenario) => findResult(scenario, model)).filter(Boolean) as Result[];
}

export function absoluteUrl(path = "/") {
  return new URL(path, SITE_URL).toString();
}

export { data };
