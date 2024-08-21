import { useEffect, useState } from "react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const BACKEND_BASE_URL = "http://localhost:8000" //import
type Job = {
  id: string,
  url: string,
  jobType: 'page_text' | 'extract'
  createdAt: string,
}
type Props = { accessToken: string }

export default function logsTable({ accessToken }: Props) {
  const [logs, setLogs] = useState<Job[]>([])

  useEffect(() => {
    const headers = { 'Authorization': `Bearer ${accessToken}`}
    fetch(`${BACKEND_BASE_URL}/jobs`, { headers })
      .then(r => r.json())
      .then(data => {
        console.log(data)
        setLogs(data)
      })
  }, [accessToken])

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[350px]">Id</TableHead>
          <TableHead>URL</TableHead>
          <TableHead>Type</TableHead>
          <TableHead className="text-right">Date</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {logs.map((job) => (
          <TableRow key={job.id}>
            <TableCell className="font-medium">{job.id}</TableCell>
            <TableCell>{job.url}</TableCell>
            <TableCell>{job.jobType}</TableCell>
            <TableCell className="text-right">{new Date(job.createdAt + 'Z').toLocaleString()}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}