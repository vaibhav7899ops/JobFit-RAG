"use client";

import { useEffect, useState } from "react";

type Job = {
  id: number;
  title: string;
  company: string;
  description: string;
  url: string;
  fetched_at: string;
};

const PAGE_SIZE = 10;

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[] | null>(null);
  const [page, setPage] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setJobs(null);
    fetch(`/api/jobs?skip=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`)
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
          setError("Could not load jobs.");
          return;
        }
        setJobs(data);
      })
      .catch(() => setError("Could not reach the server."));
  }, [page]);

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold">Browse jobs</h1>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {jobs === null ? (
        <p className="text-sm text-gray-500">Loading...</p>
      ) : jobs.length === 0 && page === 0 ? (
        <p className="text-sm text-gray-500">No jobs synced yet.</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {jobs.map((job) => (
            <li key={job.id} className="border border-gray-200 rounded-lg bg-white p-4">
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="font-semibold hover:underline"
              >
                {job.title}
              </a>
              <p className="text-sm text-gray-500 mb-2">{job.company}</p>
              <p className="text-sm text-gray-700 line-clamp-3">{job.description}</p>
            </li>
          ))}
        </ul>
      )}

      <div className="flex gap-3 items-center">
        <button
          onClick={() => setPage((p) => Math.max(0, p - 1))}
          disabled={page === 0}
          className="text-sm border border-gray-300 rounded-md px-3 py-1.5 hover:bg-gray-100 disabled:opacity-40 cursor-pointer"
        >
          Previous
        </button>
        <button
          onClick={() => setPage((p) => p + 1)}
          disabled={jobs !== null && jobs.length < PAGE_SIZE}
          className="text-sm border border-gray-300 rounded-md px-3 py-1.5 hover:bg-gray-100 disabled:opacity-40 cursor-pointer"
        >
          Next
        </button>
      </div>
    </div>
  );
}
