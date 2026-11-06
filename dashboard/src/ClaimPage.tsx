import { useCallback, useEffect, useState } from "react";
import {
  api,
  type Claim,
  type Policy,
  type PreviousClaim,
  type Step,
} from "./api";
import { AgentSteps } from "./AgentSteps";
import {
  ClaimStory,
  DecisionPanel,
  HistoryPanel,
  PolicyPanel,
} from "./ClaimDetails";
import { words } from "./format";
import { SignOffPanel } from "./SignOffPanel";
import { StatusChip } from "./StatusChip";

const pollMilliseconds = 2000;

export function ClaimPage({ claimId }: Readonly<{ claimId: string }>) {
  const [claim, setClaim] = useState<Claim | null>(null);
  const [steps, setSteps] = useState<Step[]>([]);
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [history, setHistory] = useState<PreviousClaim[] | null>(null);
  const [error, setError] = useState("");
  const [started, setStarted] = useState(false);

  const refresh = useCallback(async () => {
    const [loaded, loadedSteps] = await Promise.all([
      api.getClaim(claimId),
      api.listSteps(claimId),
    ]);
    setClaim(loaded);
    setSteps(loadedSteps);
  }, [claimId]);

  useEffect(() => {
    Promise.all([api.getClaim(claimId), api.listSteps(claimId)])
      .then(async ([loaded, loadedSteps]) => {
        setClaim(loaded);
        setSteps(loadedSteps);
        setPolicy(await api.getPolicy(loaded.policy_id));
        setHistory(await api.getClaimHistory(loaded.customer_id));
      })
      .catch((reason: unknown) => {
        setError(String(reason));
      });
  }, [claimId]);

  const status = claim?.status;
  useEffect(() => {
    if (status !== "in_progress") return;
    const timer = setInterval(() => {
      void refresh();
    }, pollMilliseconds);
    return () => {
      clearInterval(timer);
    };
  }, [status, refresh]);

  function runAgent() {
    setStarted(true);
    api
      .runAgent(claimId)
      .then(setClaim)
      .catch((reason: unknown) => {
        setError(String(reason));
      });
  }

  if (!claim) {
    return error ? (
      <p role="alert">
        Could not load {claimId}. {error}
      </p>
    ) : (
      <p>Loading {claimId}</p>
    );
  }

  const canRun =
    !started && (claim.status === "waiting" || claim.status === "in_progress");

  return (
    <>
      <p>
        <a href="#/">Back to the queue</a>
      </p>
      <h1>
        <span className="mono">{claim.claim_id}</span> {claim.summary}
      </h1>
      <div className="claim-meta">
        <StatusChip status={claim.status} /> {words(claim.claim_type)}
        {canRun && (
          <button type="button" onClick={runAgent}>
            Run agent
          </button>
        )}
      </div>
      {error && <p role="alert">{error}</p>}
      {claim.status === "waiting_for_signoff" && (
        <SignOffPanel claim={claim} onSignedOff={setClaim} />
      )}
      <DecisionPanel claim={claim} />
      <AgentSteps steps={steps} working={claim.status === "in_progress"} />
      <div className="columns">
        <ClaimStory claim={claim} />
        <div>
          {policy && <PolicyPanel policy={policy} />}
          {history && <HistoryPanel history={history} />}
        </div>
      </div>
    </>
  );
}
