import Link from "next/link";

import { AuthCard } from "@/components/auth/auth-card";
import { AuthForm } from "@/components/auth/auth-form";

export default function LoginPage() {
  return (
    <AuthCard
      description="Pick up where you left off and keep moving toward work that fits."
      eyebrow="Welcome back"
      footer={
        <>
          New to Career Compass? <Link href="/signup">Create an account</Link>
        </>
      }
      title="Sign in to your path."
    >
      <AuthForm mode="login" />
    </AuthCard>
  );
}
