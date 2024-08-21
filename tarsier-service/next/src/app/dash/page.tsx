"use client"
import { useRouter } from "next/navigation";
import { withAuthInfo, type WithAuthInfoProps } from "@propelauth/react"
import { Button } from "@/components/ui/button";
import LogsTable from "@/components/apiLogsTable"


const Dashboard = withAuthInfo((props: WithAuthInfoProps) => {
  const router = useRouter()

  const manageApiKeys = () => {
    router.push("https://6966894145.propelauthtest.com/api_keys/personal")
  }

  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex justify-between p-3 items-center border-b border-gray-300">
        <div className="pr">Tarsier Service</div>
        <div>
          <a href="https://tarsier.mintlify.app" target="_blank">
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
          <div className="font-bold text-3xl mb-8">Jobs Log</div>
            { props.accessToken && <LogsTable accessToken={props.accessToken} /> }
        </div>
      </div>
    </div>
  );
})
export default Dashboard