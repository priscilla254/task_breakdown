export const DEFAULT_PROJECT_ID = "phase1";

export const PROJECTS = [
  {
    id: "phase1",
    title: "Data science and Innovation",
    highlight: "Phase 1",
    subtitle: "Excel → database → API → Power BI rollout",
    tabLabel: "Data science & Innovation",
  },
  {
    id: "training",
    title: "Training platform content",
    highlight: null,
    subtitle: "Training platform rollout — same structure as Phase 1",
    tabLabel: "Training platform",
  },
];

export function getProject(id) {
  return PROJECTS.find((p) => p.id === id) ?? PROJECTS[0];
}
