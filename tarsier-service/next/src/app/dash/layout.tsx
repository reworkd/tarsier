"use client"
import { RequiredAuthProvider, RedirectToLogin } from "@propelauth/react";
import { Toaster } from "@/components/ui/toaster"

export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {  
  return (
    <html>
      <body>
        <RequiredAuthProvider 
          authUrl="https://6966894145.propelauthtest.com"
          displayIfLoggedOut={<RedirectToLogin />}
        >
          {children}
        </RequiredAuthProvider>
        <Toaster />
      </body>
    </html>
  );
}