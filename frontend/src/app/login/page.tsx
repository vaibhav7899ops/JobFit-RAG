import Link from "next/link";
import AuthForm from "@/components/AuthForm";

export default function LoginPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-center">Log in</h1>
      <AuthForm mode="login" />
      <p className="text-sm text-center text-gray-600">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="text-gray-900 font-medium hover:underline">
          Sign up
        </Link>
      </p>
    </div>
  );
}
