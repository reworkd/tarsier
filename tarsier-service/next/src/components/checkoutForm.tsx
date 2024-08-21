import React, { useCallback, useState } from "react";
import {loadStripe} from '@stripe/stripe-js'
import {
  EmbeddedCheckoutProvider,
  EmbeddedCheckout
} from '@stripe/react-stripe-js'
import {
  Dialog,
  DialogContent,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button";
import { BACKEND_BASE } from "@/constants/api"

const stripePromise = loadStripe("pk_test_51MeqhXHyVxfGsTbD1iFVkxh1vEU0RlRrmypARJsqLgHWBkJ0YwbkFHAyjxO3wOPJ0nXeVZjSMO8I1P6B7gw747gZ00pvLoiiJ0");

type Props = { accessToken: string }
const CheckoutForm = ({ accessToken }: Props) => {

  const [checkoutOpen, setCheckoutOpen] = useState(false)

  const fetchClientSecret = useCallback(() => {
    const headers = { Authorization: `Bearer ${accessToken}`}
    return fetch(`${BACKEND_BASE}/create-checkout-session`, {
      headers,
      method: "POST",
    })
      .then((res) => res.json())
      .then((data) => data.clientSecret);
  }, []);

  const options = { fetchClientSecret };
//absolute inset-0 bg-white z-50
  return (
    <>
      <Dialog>
        <DialogTrigger asChild>
          <Button variant="secondary" onClick={() => setCheckoutOpen(true)}>Buy Subscription</Button>
        </DialogTrigger>
        <DialogContent className="max-w-[1200px] w-full max-h-screen overflow-auto">
          { checkoutOpen &&
            <div id="checkout" className="">
              <EmbeddedCheckoutProvider
                stripe={stripePromise}
                options={options}
              >
                <EmbeddedCheckout />
              </EmbeddedCheckoutProvider>
            </div>
          }
        </DialogContent>
      </Dialog>
    </>
  )
}

export default CheckoutForm