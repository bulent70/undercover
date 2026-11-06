import { rmSync } from "node:fs";
import { databaseFile } from "../playwright.config";

export default function globalSetup() {
  rmSync(databaseFile, { force: true });
}
