import { LoginForm } from "@/components/auth/login-form";
import { LoginHero } from "@/components/auth/login-hero";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen">
      <LoginHero />

      <div className="flex w-full lg:w-1/2 items-center justify-center p-8 bg-background">
        <LoginForm />
      </div>
    </div>
  );
}
