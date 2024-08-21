"use client"
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { DEMO_PAGE_TEXT } from "@/constants/marketingPage";
import Image from "next/image";

export default function Home() {
  const router = useRouter()
  const signIn = () => {
    router.push("https://6966894145.propelauthtest.com")
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="text-end p-3">
        <Button onClick={signIn}>Sign in</Button>
      </div>
      <div className="text-start pt-10">
        <div className="font-bold text-3xl pb-4">Tarsier Service</div>
        <div className="relative">
          <div className="whitespace-pre text-xs border border-black rounded-md p-2 overflow-clip">{ DEMO_PAGE_TEXT }</div>
          <Image 
            className="absolute top-0 h-full w-full"
            src="/hn_ss.png" 
            width={2169}
            height={1234}
            alt="hacker news screenshot" 
          />
        </div>
      </div>
    </div>
  );
}
