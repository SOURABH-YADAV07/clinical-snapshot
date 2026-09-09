"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/patients", label: "Patients" },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link href="/" className="navbar-brand">
          Clinical Snapshot
        </Link>
        <div className="navbar-links">
          {LINKS.map((link) => {
            const isActive = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
            return (
              <Link key={link.href} href={link.href} className={isActive ? "navbar-link active" : "navbar-link"}>
                {link.label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
