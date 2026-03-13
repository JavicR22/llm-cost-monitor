import type { Metadata } from "next";
import { Public_Sans } from "next/font/google";

const publicSans = Public_Sans({
  subsets: ["latin"],
  variable: "--font-public-sans",
});

export const metadata: Metadata = {
  title: "LLM Cost Monitor",
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className={`${publicSans.variable} font-[family-name:var(--font-public-sans)]`}>
      {children}
    </div>
  );
}
