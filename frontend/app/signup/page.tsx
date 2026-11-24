import Link from "next/link";

import { AuthCard } from "@/components/auth/auth-card";
import { AuthForm } from "@/components/auth/auth-form";

export default function SignupPage() {
  return (
    <AuthCard
      description="Create your account to save your goals, explore roles, and shape your next steps."
      eyebrow="Start with a direction"
      footer={
        <>
          Already have an account? <Link href="/login">Sign in</Link>
        </>
      }
      title="Make room for what’s next."
    >
      <AuthForm mode="signup" />
    </AuthCard>
  );
}
