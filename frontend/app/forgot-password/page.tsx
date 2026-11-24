import { AuthCard } from "@/components/auth/auth-card";
import { PasswordRecoveryRequest } from "@/components/auth/password-recovery";

export default function ForgotPasswordPage() {
  return (
    <AuthCard
      description="We’ll send a secure recovery link if an account matches that email."
      eyebrow="Account recovery"
      footer="Your password is managed securely by Supabase."
      title="Let’s get you back in."
    >
      <PasswordRecoveryRequest />
    </AuthCard>
  );
}
