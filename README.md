# GenLayer Freelancer Market

A decentralized freelancer marketplace where an AI verifies if delivered work meets the job requirements before payment is released. Built on GenLayer Testnet Bradbury.

---

## What is this

I built this because the biggest problem in freelancing is disputes over whether the work was actually completed as agreed. With a normal platform you need a human arbitrator or you just trust one side over the other. With GenLayer the AI reads the actual deliverable and checks it against the requirements that were agreed upfront, and multiple validators have to agree on the verdict before anything is finalized.

The idea is simple. A client posts a job with a description and a list of requirements. A freelancer accepts and delivers a URL pointing to the work. The contract fetches that URL and an AI judge decides if the requirements were met. If not, the freelancer can resubmit with an improved deliverable.

---

## How it works

The client posts a job with a title, description, and requirements. The freelancer accepts the job and their address gets recorded. When the work is done the freelancer submits a deliverable URL. Anyone can then trigger the AI verification which fetches the deliverable content and evaluates it against the requirements. The verdict is APPROVED or REJECTED with a confidence score and reasoning explaining which requirements were or were not met.

If the work is rejected the freelancer can resubmit a new deliverable URL and trigger verification again.

---

## Functions

post_job takes a title, description, and requirements and creates a new job in open status.

accept_job takes a job id and a freelancer address and moves the job to in_progress.

submit_deliverable takes a job id and a URL pointing to the delivered work.

verify_deliverable takes a job id and triggers the AI evaluation through Optimistic Democracy consensus. The AI fetches the deliverable URL and checks it against the requirements.

resubmit_deliverable takes a job id and a new deliverable URL if the previous submission was rejected.

get_job shows the full job state including client, freelancer, status, deliverable URL, verdict, and reasoning.

---

## Test results

Posted a job for building a landing page with a hero section, feature blocks, contact form, and mobile responsiveness. Submitted a Wikipedia article as the deliverable. The AI correctly rejected it both times noting that a Wikipedia page does not contain any of the required landing page elements. The reasoning was specific and accurate each time.

---

## How to run it

Go to GenLayer Studio at https://studio.genlayer.com and create a new file called freelancer_market.py. Paste the contract code and set execution mode to Normal Full Consensus. Deploy with your address as owner_address.

Follow this order and wait for FINALIZED at each step. Run get_summary first, then post_job, then accept_job with a freelancer address, then submit_deliverable with a URL, then verify_deliverable to trigger the AI check, then get_job to see the verdict. If rejected you can run resubmit_deliverable and verify_deliverable again.

Note: the contract in this repository uses the Address type in the constructor as required by genvm-lint. When deploying in GenLayer Studio use a version that receives str in the constructor and converts internally with Address(owner_address) since Studio requires primitive types to parse the contract schema correctly.

---

## Resources

GenLayer Docs: https://docs.genlayer.com

Optimistic Democracy: https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/optimistic-democracy

Equivalence Principle: https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/optimistic-democracy/equivalence-principle

GenLayer Studio: https://studio.genlayer.com

Discord: https://discord.gg/8Jm4v89VAu
