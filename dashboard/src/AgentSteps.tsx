import type { Step } from "./api";

const kindLabels: Record<Step["kind"], string> = {
  model: "Agent",
  tool_call: "Calls",
  tool_result: "Result",
};

const resultLength = 400;

function shorten(step: Step): string {
  if (step.kind !== "tool_result" || step.text.length <= resultLength) {
    return step.text;
  }
  return `${step.text.slice(0, resultLength)}…`;
}

export function AgentSteps({
  steps,
  working,
}: Readonly<{ steps: Step[]; working: boolean }>) {
  if (steps.length === 0 && !working) return null;
  return (
    <section className="panel" aria-label="Agent steps">
      <h2>What the agent did</h2>
      {working && <p className="muted">The agent is working on this claim.</p>}
      <ol className="steps">
        {steps.map((step) => (
          <li key={step.step_id}>
            <span className="step-kind">{kindLabels[step.kind]}</span>
            <span className="step-text">{shorten(step)}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
