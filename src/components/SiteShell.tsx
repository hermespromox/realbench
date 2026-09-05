import Link from "next/link";
import styles from "./shell.module.css";

export default function SiteShell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className={styles.nav}>
        <Link className={styles.brand} href="/" aria-label="RealBench home">
          <span className={styles.mark} aria-hidden="true">RB</span>
          <span>
            <strong>RealBench</strong>
            <small>Frontend capability benchmark</small>
          </span>
        </Link>
        <nav className={styles.links} aria-label="Primary">
          <Link href="/#arena">Arena</Link>
          <Link href="/library">Library</Link>
          <Link href="/#methodology">Methodology</Link>
          <a href="https://github.com/hermespromox/realbench" target="_blank" rel="noreferrer">GitHub</a>
        </nav>
      </header>
      {children}
      <footer className={styles.footer}>
        <p>IBM Carbon-inspired visual system. One-shot HTML artifacts, published as generated.</p>
        <p>© {new Date().getFullYear()} RealBench</p>
      </footer>
    </>
  );
}
