import { useEffect, useState } from "react";
import { api, type Claim, type Handler } from "./api";
import { money } from "./format";

export function SignOffPanel({
  claim,
  onSignedOff,
}: Readonly<{ claim: Claim; onSignedOff: (claim: Claim) => void }>) {
  const [handlers, setHandlers] = useState<Handler[]>([]);
  const [handlerId, setHandlerId] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    void api.listHandlers().then((loaded) => {
      setHandlers(loaded);
      setHandlerId(loaded[0]?.handler_id ?? "");
    });
  }, []);

  function signOff() {
    api
      .signOff(claim.claim_id, handlerId)
      .then(onSignedOff)
      .catch((reason: unknown) => {
        setError(String(reason));
      });
  }

  return (
    <section className="panel" aria-label="Sign-off">
      <h2>Waiting for sign-off</h2>
      <p>
        The payout of{" "}
        <span className="mono">{money(claim.decision?.payout ?? 0)}</span> is
        over the approval limit. A handler must sign off before it is paid.
      </p>
      <div className="actions">
        <label>
          Handler{" "}
          <select
            value={handlerId}
            onChange={(event) => {
              setHandlerId(event.target.value);
            }}
          >
            {handlers.map((handler) => (
              <option key={handler.handler_id} value={handler.handler_id}>
                {handler.name}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={signOff} disabled={!handlerId}>
          Sign off and pay
        </button>
      </div>
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
