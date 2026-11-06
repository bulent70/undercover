import { useEffect, useState } from "react";
import { api, type Claim, type Policy, type PreviousClaim } from "./api";
import {
  ClaimStory,
  DecisionPanel,
  HistoryPanel,
  PolicyPanel,
} from "./ClaimDetails";
import { words } from "./format";
import { StatusChip } from "./StatusChip";

export function ClaimPage({ claimId }: Readonly<{ claimId: string }>) {
  const [claim, setClaim] = useState<Claim | null>(null);
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [history, setHistory] = useState<PreviousClaim[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getClaim(claimId)
      .then(async (loaded) => {
        setClaim(loaded);
        setPolicy(await api.getPolicy(loaded.policy_id));
        setHistory(await api.getClaimHistory(loaded.customer_id));
      })
      .catch((reason: unknown) => {
        setError(String(reason));
      });
  }, [claimId]);

  if (error)
    return (
      <p role="alert">
        Could not load {claimId}. {error}
      </p>
    );
  if (!claim) return <p>Loading {claimId}</p>;

  return (
    <>
      <p>
        <a href="#/">Back to the queue</a>
      </p>
      <h1>
        <span className="mono">{claim.claim_id}</span> {claim.summary}
      </h1>
      <p className="claim-meta">
        <StatusChip status={claim.status} /> {words(claim.claim_type)}
      </p>
      <DecisionPanel claim={claim} />
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
