"use client"
import { useRouter, useSearchParams } from "next/navigation";
import { withAuthInfo, type WithAuthInfoProps } from "@propelauth/react"
import { Button } from "@/components/ui/button";
import LogsTable from "@/components/apiLogsTable"
import CheckoutForm from "@/components/checkoutForm";
import { useToast } from "@/components/ui/use-toast"
import { useEffect, useState } from "react";
import { BACKEND_BASE } from "@/constants/api";

const Dashboard = withAuthInfo((props: WithAuthInfoProps) => {
  const requestLimit: number = (props.user as any)?.metadata?.request_limit || 100
  const router = useRouter()
  const searchParams = useSearchParams()
  const { toast } = useToast()
  const [jobsThisMonth, setJobsThisMonth] = useState<'?' | number>('?')


  if (searchParams.get("session_id")) {
    toast({ "title": "Payment Successful", "description": "API monthly limit set to 1000", "className": "bg-black text-white" })
    router.replace("/dash");
  }

  useEffect(() => {
    const headers = { 'Authorization': `Bearer ${props.accessToken}`}
    fetch(`${BACKEND_BASE}/job-count-cur-month`, { headers })
      .then(r => r.json())
      .then(count => {
        setJobsThisMonth(count)
      })
  }, [])

  const manageApiKeys = () => {
    router.push("https://6966894145.propelauthtest.com/api_keys/personal")
  }

  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex justify-between p-3 items-center border-b border-gray-300">
        <div className="pr">Tarsier Service</div>
        <div>
          <CheckoutForm accessToken={props.accessToken!} />
          <a href="https://tarsier.mintlify.app" target="_blank" className="ml-4">
            <Button variant="secondary">Docs</Button>
          </a>
          <Button className="ml-4" onClick={manageApiKeys}>Create API Key</Button>
        </div>
      </div>
      <div className="flex flex-row flex-1">
        <div className="bg-gray-100 w-80 py-2 border-r border-gray-300">
          <div className="text-center">{ props.user?.email }</div>
        </div>
        <div className="flex-1 p-8">
          <div className="mb-8 flex justify-between">
            <div className="font-bold text-3xl ">Jobs Log</div>
            <div>This month: {jobsThisMonth} / { requestLimit }</div>
          </div>
            { props.accessToken && <LogsTable accessToken={props.accessToken} /> }
        </div>
      </div>
    </div>
  );
})
export default Dashboard