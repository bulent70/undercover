import { useEffect, useState } from "react";

function currentRoute(): string {
  return window.location.hash.replace(/^#/, "") || "/";
}

export function useHashRoute(): string {
  const [route, setRoute] = useState(currentRoute);

  useEffect(() => {
    const update = () => {
      setRoute(currentRoute());
    };
    window.addEventListener("hashchange", update);
    return () => {
      window.removeEventListener("hashchange", update);
    };
  }, []);

  return route;
}
