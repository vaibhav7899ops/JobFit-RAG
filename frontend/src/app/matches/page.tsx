"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type SkillMatch = {
  name: string;
  reason: string;
};

type Match = {
  id: number;
  job_id: number;
  score: number;
  analysis_json: {
    matching_skills: SkillMatch[];
    missing_skills: SkillMatch[];
    summary: string;
  };
  calculated_at: string;
};

function scoreColor(score: number): string {
  if (score >= 70) return "bg-green-100 text-green-800";
  if (score >= 40) return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-800";
}

export default function MatchesPage() {
  const [matches, setMatches] = useState<Match[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch("/api/matches")
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
          setError(typeof data.detail === "string" ? data.detail : "Something went wrong");
          return;
        }
        setMatches(data);
      })
      .catch(() => setError("Could not reach the server. Please try again."))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return <p className="text-sm text-gray-500">Finding your best-fit jobs, this can take a few seconds...</p>;
  }

  if (error) {
    return (
      <div className="flex flex-col gap-3">
        <p className="text-sm text-red-600">{error}</p>
        <Link href="/upload" className="text-sm text-gray-900 font-medium hover:underline w-fit">
          Go upload a resume &rarr;
        </Link>
      </div>
    );
  }

  const sortedMatches = [...(matches ?? [])].sort((a, b) => b.score - a.score);

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold">Your matches</h1>
      {sortedMatches.length === 0 ? (
        <p className="text-sm text-gray-500">No matches yet.</p>
      ) : (
        <ul className="flex flex-col gap-4">
          {sortedMatches.map((match) => (
            <li key={match.id} className="border border-gray-200 rounded-lg bg-white p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-500">Job #{match.job_id}</span>
                <span className={`text-sm font-semibold px-2 py-0.5 rounded-full ${scoreColor(match.score)}`}>
                  {match.score}/100
                </span>
              </div>
              <p className="text-sm text-gray-800 mb-3">{match.analysis_json.summary}</p>
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Matching skills</p>
                  <ul className="flex flex-col gap-1">
                    {match.analysis_json.matching_skills.map((skill) => (
                      <li key={skill.name} className="text-sm">
                        <span className="font-medium">{skill.name}</span>
                        <span className="text-gray-500"> &mdash; {skill.reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Missing skills</p>
                  {match.analysis_json.missing_skills.length === 0 ? (
                    <p className="text-sm text-gray-500">None &mdash; great fit!</p>
                  ) : (
                    <ul className="flex flex-col gap-1">
                      {match.analysis_json.missing_skills.map((skill) => (
                        <li key={skill.name} className="text-sm">
                          <span className="font-medium">{skill.name}</span>
                          <span className="text-gray-500"> &mdash; {skill.reason}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
