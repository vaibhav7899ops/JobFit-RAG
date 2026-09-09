import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import { cookies } from "next/headers";
import "./globals.css";
import { AUTH_COOKIE_NAME } from "@/lib/backend";
import LogoutButton from "@/components/LogoutButton";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "JobFit-RAG",
  description: "Resume-to-job matching",
};

export default async function RootLayout({ children }: LayoutProps<"/">) {
  const cookieStore = await cookies();
  const isAuthenticated = Boolean(cookieStore.get(AUTH_COOKIE_NAME)?.value);

  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-gray-50 text-gray-900">
        <header className="border-b border-gray-200 bg-white">
          <nav className="max-w-4xl mx-auto flex items-center justify-between px-4 py-3">
            <Link href="/" className="font-semibold">
              JobFit-RAG
            </Link>
            <div className="flex items-center gap-5">
              <Link href="/jobs" className="text-sm text-gray-600 hover:text-gray-900">
                Jobs
              </Link>
              {isAuthenticated ? (
                <>
                  <Link href="/matches" className="text-sm text-gray-600 hover:text-gray-900">
                    Matches
                  </Link>
                  <Link href="/upload" className="text-sm text-gray-600 hover:text-gray-900">
                    Upload Resume
                  </Link>
                  <LogoutButton />
                </>
              ) : (
                <>
                  <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">
                    Log in
                  </Link>
                  <Link
                    href="/signup"
                    className="text-sm bg-gray-900 text-white px-3 py-1.5 rounded-md hover:bg-gray-700"
                  >
                    Sign up
                  </Link>
                </>
              )}
            </div>
          </nav>
        </header>
        <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
