import { AuthCard } from "@/components/auth/auth-card";
import { UpdatePasswordForm } from "@/components/auth/password-recovery";

export default function UpdatePasswordPage() {
  return (
    <AuthCard
      description="Choose a new password for your Career Compass sign-in."
      eyebrow="Secure your account"
      footer="Password recovery is handled by Supabase Auth."
      title="Set a new password."
    >
      <UpdatePasswordForm />
    </AuthCard>
  );
}
