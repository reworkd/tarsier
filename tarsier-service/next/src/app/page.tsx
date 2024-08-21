"use client"
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

export default function Home() {
  const router = useRouter()
  const signIn = () => {
    router.push("https://6966894145.propelauthtest.com")
  }

  return (
    <div className="mx-auto max-w-4xl">
      <div className="text-end p-3">
        <Button onClick={signIn}>Sign in</Button>
      </div>
      <div className="text-center py-20">
        <div className="font-bold text-4xl">Tarsier Service</div>
      </div>
    </div>
  );
}
