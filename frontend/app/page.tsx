import { redirect } from "next/navigation";

// Ask is home. It is the only page that answers a question — everything else is
// what you tell the system or a record of what it told you. A signed-out visitor
// bounces on to /login from Shell's auth guard; a new account is sent to
// /welcome by the first-run gate.
export default function Home() {
  redirect("/chat");
}
