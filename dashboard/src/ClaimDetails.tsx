import type { Claim, Policy, PreviousClaim } from "./api";
import { date, decisionLabels, money, words } from "./format";

export function DecisionPanel({ claim }: Readonly<{ claim: Claim }>) {
  const { decision, payment } = claim;
  if (!decision) return null;
  return (
    <section className="panel" aria-label="Decision">
      <h2>
        <span className={`decision decision-${decision.decision}`}>
          {decisionLabels[decision.decision]}
        </span>{" "}
        <span className="mono">{money(decision.payout)}</span>
      </h2>
      <p className="reason">{decision.reason}</p>
      <p className="muted">Policy wording: {decision.section}</p>
      {payment && (
        <p>
          Paid <span className="mono">{money(payment.amount)}</span> on{" "}
          {date(payment.paid_at)}
          {payment.handler_id && ` with sign-off by ${payment.handler_id}`}
        </p>
      )}
    </section>
  );
}

export function ClaimStory({ claim }: Readonly<{ claim: Claim }>) {
  return (
    <section className="panel">
      <h2>The customer's story</h2>
      <p className="muted">
        Incident on {date(claim.incident_date)} in {claim.incident_location}.
        Submitted {date(claim.submitted_on)}.
      </p>
      <blockquote>{claim.story}</blockquote>
      <h3>Items claimed</h3>
      <table>
        <tbody>
          {claim.items.map((item) => (
            <tr key={item.description}>
              <td>{item.description}</td>
              <td>{words(item.category)}</td>
              <td className="number mono">{money(item.amount)}</td>
            </tr>
          ))}
          <tr className="total">
            <td colSpan={2}>Total claimed</td>
            <td className="number mono">{money(claim.amount_claimed)}</td>
          </tr>
        </tbody>
      </table>
      <h3>Documents</h3>
      {claim.documents.map((document) => (
        <details key={document.name}>
          <summary>{document.name}</summary>
          <p>{document.content}</p>
        </details>
      ))}
    </section>
  );
}

export function PolicyPanel({ policy }: Readonly<{ policy: Policy }>) {
  return (
    <section className="panel" aria-label="Policy">
      <h2>
        Policy <span className="mono">{policy.policy_id}</span>
      </h2>
      <dl>
        <dt>Plan</dt>
        <dd>{words(policy.plan)}</dd>
        <dt>Add-ons</dt>
        <dd>{policy.add_ons.map(words).join(", ") || "None"}</dd>
        <dt>Bought</dt>
        <dd>
          {date(policy.purchased_on)} through {policy.sold_through}
        </dd>
        <dt>Trip</dt>
        <dd>
          {policy.trip.destination}, {date(policy.trip.departs_on)} to{" "}
          {date(policy.trip.returns_on)}
        </dd>
        <dt>Trip cost</dt>
        <dd className="mono">{money(policy.trip.trip_cost)}</dd>
        <dt>Travelers</dt>
        <dd>{policy.travelers.join(", ")}</dd>
      </dl>
    </section>
  );
}

export function HistoryPanel({
  history,
}: Readonly<{ history: PreviousClaim[] }>) {
  return (
    <section className="panel" aria-label="Claim history">
      <h2>Claim history</h2>
      {history.length === 0 ? (
        <p className="muted">No previous claims.</p>
      ) : (
        <ul className="history">
          {history.map((previous) => (
            <li key={previous.claim_id}>
              <span className="mono">{previous.claim_id}</span>{" "}
              {date(previous.filed_on)}: {previous.summary}.{" "}
              {words(previous.outcome)}, paid{" "}
              <span className="mono">{money(previous.amount_paid)}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
