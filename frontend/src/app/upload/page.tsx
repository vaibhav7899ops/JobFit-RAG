"use client";

import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";

type Resume = {
  id: number;
  raw_text: string;
  uploaded_at: string;
};

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [resumes, setResumes] = useState<Resume[] | null>(null);

  async function loadResumes() {
    const response = await fetch("/api/resumes");
    if (response.ok) {
      setResumes(await response.json());
    }
  }

  useEffect(() => {
    loadResumes();
  }, []);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
    setError(null);
    setSuccessMessage(null);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file) return;

    setError(null);
    setSuccessMessage(null);
    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.set("file", file);

      const response = await fetch("/api/resumes/upload", { method: "POST", body: formData });
      const data = await response.json();

      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Upload failed");
        return;
      }

      setSuccessMessage("Resume uploaded successfully.");
      setFile(null);
      await loadResumes();
    } catch {
      setError("Could not reach the server. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-bold mb-4">Upload your resume</h1>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 max-w-sm">
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={handleFileChange}
            className="text-sm file:mr-4 file:rounded-md file:border-0 file:bg-gray-900 file:text-white file:px-3 file:py-2 file:text-sm file:cursor-pointer"
          />
          <p className="text-xs text-gray-500">PDF or DOCX, up to 5MB.</p>
          {error && <p className="text-sm text-red-600">{error}</p>}
          {successMessage && <p className="text-sm text-green-700">{successMessage}</p>}
          <button
            type="submit"
            disabled={!file || isSubmitting}
            className="bg-gray-900 text-white rounded-md py-2 text-sm font-medium hover:bg-gray-700 disabled:opacity-50 cursor-pointer w-fit px-4"
          >
            {isSubmitting ? "Uploading..." : "Upload"}
          </button>
        </form>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-3">Upload history</h2>
        {resumes === null ? (
          <p className="text-sm text-gray-500">Loading...</p>
        ) : resumes.length === 0 ? (
          <p className="text-sm text-gray-500">No resumes uploaded yet.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {resumes.map((resume) => (
              <li key={resume.id} className="border border-gray-200 rounded-md p-3 bg-white">
                <p className="text-xs text-gray-500 mb-1">
                  Uploaded {new Date(resume.uploaded_at).toLocaleString()}
                </p>
                <p className="text-sm text-gray-800 line-clamp-2">{resume.raw_text}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
