import Link from "next/link";
import AuthForm from "@/components/AuthForm";

export default function SignupPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-center">Create an account</h1>
      <AuthForm mode="signup" />
      <p className="text-sm text-center text-gray-600">
        Already have an account?{" "}
        <Link href="/login" className="text-gray-900 font-medium hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
