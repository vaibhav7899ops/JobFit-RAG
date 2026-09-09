import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col items-center text-center gap-6 py-16">
      <h1 className="text-3xl font-bold">Find your best-fit jobs, instantly</h1>
      <p className="text-gray-600 max-w-md">
        Upload your resume and JobFit-RAG will match it against real job listings, scoring each
        one and explaining exactly why it fits &mdash; or doesn&apos;t.
      </p>
      <div className="flex gap-3">
        <Link
          href="/signup"
          className="bg-gray-900 text-white px-4 py-2 rounded-md hover:bg-gray-700"
        >
          Get started
        </Link>
        <Link
          href="/jobs"
          className="border border-gray-300 px-4 py-2 rounded-md hover:bg-gray-100"
        >
          Browse jobs
        </Link>
      </div>
    </div>
  );
}
