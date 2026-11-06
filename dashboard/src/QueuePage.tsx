import { useCallback, useEffect, useState } from "react";
import { api, type ClaimSummary, type Status } from "./api";
import { date, money, statusLabels, words } from "./format";
import { StatusChip } from "./StatusChip";

const statuses = Object.keys(statusLabels) as Status[];
const pollMilliseconds = 2000;

export function QueuePage() {
  const [claims, setClaims] = useState<ClaimSummary[] | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api
      .listClaims()
      .then(setClaims)
      .catch((reason: unknown) => {
        setError(String(reason));
      });
  }, []);

  useEffect(load, [load]);

  const working = claims?.some((claim) => claim.status === "in_progress");
  useEffect(() => {
    if (!working) return;
    const timer = setInterval(load, pollMilliseconds);
    return () => {
      clearInterval(timer);
    };
  }, [working, load]);

  if (error) return <p role="alert">Could not load the queue. {error}</p>;
  if (!claims) return <p>Loading the queue</p>;

  return (
    <>
      <h1>Claims queue</h1>
      <ul className="tiles" aria-label="Claims by state">
        {statuses.map((status) => (
          <li key={status} className={`tile tile-${status}`}>
            <span className="tile-count">
              {claims.filter((claim) => claim.status === status).length}
            </span>
            <span>{statusLabels[status]}</span>
          </li>
        ))}
      </ul>
      <section className="panel">
        <table>
          <thead>
            <tr>
              <th scope="col">Claim</th>
              <th scope="col">Summary</th>
              <th scope="col">Type</th>
              <th scope="col">Submitted</th>
              <th scope="col" className="number">
                Claimed
              </th>
              <th scope="col">State</th>
            </tr>
          </thead>
          <tbody>
            {claims.map((claim) => (
              <tr key={claim.claim_id}>
                <td className="mono">
                  <a href={`#/claims/${claim.claim_id}`}>{claim.claim_id}</a>
                </td>
                <td>{claim.summary}</td>
                <td>{words(claim.claim_type)}</td>
                <td className="nowrap">{date(claim.submitted_on)}</td>
                <td className="number mono">{money(claim.amount_claimed)}</td>
                <td>
                  <StatusChip status={claim.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
