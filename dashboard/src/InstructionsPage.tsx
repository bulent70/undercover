import { useEffect, useState } from "react";
import { api } from "./api";

export function InstructionsPage() {
  const [text, setText] = useState<string | null>(null);

  useEffect(() => {
    void api.getInstructions().then((instructions) => {
      setText(instructions.text);
    });
  }, []);

  return (
    <>
      <h1>The agent's instructions</h1>
      <p className="muted">
        Read only. The UnderCover Agent works from these instructions on every
        claim.
      </p>
      <section className="panel">
        {text === null ? (
          <p>Loading the instructions</p>
        ) : (
          <div className="instructions" aria-label="Instructions">
            {text}
          </div>
        )}
      </section>
    </>
  );
}
