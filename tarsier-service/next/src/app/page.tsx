"use client"
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { DEMO_PAGE_TEXT } from "@/constants/marketingPage";
import Image from "next/image";
import { useState } from "react";

export default function Home() {
  const router = useRouter()
  const [showImg, setShowImg] = useState(true)

  const signIn = () => {
    router.push("https://6966894145.propelauthtest.com")
  }


  return (
    <div className="mx-auto max-w-[1500px]">
      <div className="text-end p-3">
        <Button onClick={signIn}>Sign in</Button>
      </div>
      <div className="pt-10">
        <div className="pb-4 flex justify-between w-full">
          <Button variant="outline" onClick={() => setShowImg(a => !a)}>Demo</Button>
          <div className="font-bold text-3xl">Tarsier Service</div>
          <span></span>
        </div>
        <div className="relative">
          <div className="whitespace-pre text-xs border border-black rounded-md p-2 overflow-clip">{ DEMO_PAGE_TEXT }</div>
          <Image 
            className="absolute top-0 h-full w-full transition-opacity duration-300"
            style={showImg ? { } : {opacity: 0}}
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
