import { ClaimPage } from "./ClaimPage";
import { InstructionsPage } from "./InstructionsPage";
import { QueuePage } from "./QueuePage";
import { useHashRoute } from "./useHashRoute";

function Page({ route }: Readonly<{ route: string }>) {
  const claim = /^\/claims\/([\w-]+)$/.exec(route);
  if (claim) return <ClaimPage key={claim[1]} claimId={claim[1]} />;
  if (route === "/instructions") return <InstructionsPage />;
  return <QueuePage />;
}

export function App() {
  const route = useHashRoute();
  return (
    <>
      <header className="masthead">
        <a className="brand" href="#/">
          UnderCover <span className="tagline">Claims</span>
        </a>
        <nav aria-label="Main">
          <a href="#/" aria-current={route === "/" ? "page" : undefined}>
            Queue
          </a>
          <a
            href="#/instructions"
            aria-current={route === "/instructions" ? "page" : undefined}
          >
            Agent instructions
          </a>
        </nav>
      </header>
      <main>
        <Page route={route} />
      </main>
    </>
  );
}
