# { "Depends": "py-genlayer:test" }

import json
from genlayer import *


class FreelancerMarket(gl.Contract):

    owner: Address
    job_counter: u256
    job_data: DynArray[str]

    def __init__(self, owner_address: str):
        self.owner = Address(owner_address)
        self.job_counter = u256(0)

    @gl.public.view
    def get_job(self, job_id: str) -> str:
        title = self._get(job_id, "title")
        if not title:
            return "Job not found"
        return (
            f"ID: {job_id} | "
            f"Title: {title} | "
            f"Client: {self._get(job_id, 'client')} | "
            f"Freelancer: {self._get(job_id, 'freelancer')} | "
            f"Status: {self._get(job_id, 'status')} | "
            f"Deliverable: {self._get(job_id, 'deliverable_url')} | "
            f"Verdict: {self._get(job_id, 'verdict')} | "
            f"Reasoning: {self._get(job_id, 'reasoning')}"
        )

    @gl.public.view
    def get_job_count(self) -> u256:
        return self.job_counter

    @gl.public.view
    def get_summary(self) -> str:
        return (
            f"GenLayer Freelancer Market\n"
            f"Total Jobs: {int(self.job_counter)}"
        )

    @gl.public.write
    def post_job(
        self,
        title: str,
        description: str,
        requirements: str,
    ) -> str:
        caller = str(gl.message.sender_address)
        job_id = str(int(self.job_counter))

        self._set(job_id, "title", title)
        self._set(job_id, "description", description[:500])
        self._set(job_id, "requirements", requirements[:500])
        self._set(job_id, "client", caller)
        self._set(job_id, "freelancer", "")
        self._set(job_id, "status", "open")
        self._set(job_id, "deliverable_url", "")
        self._set(job_id, "verdict", "")
        self._set(job_id, "reasoning", "")

        self.job_counter = u256(int(self.job_counter) + 1)
        return f"Job {job_id} posted: {title}"

    @gl.public.write
    def accept_job(self, job_id: str, freelancer_address: str) -> str:
        assert self._get(job_id, "status") == "open", "Job is not open"

        self._set(job_id, "freelancer", freelancer_address)
        self._set(job_id, "status", "in_progress")

        return f"Job {job_id} accepted by {freelancer_address[:10]}..."

    @gl.public.write
    def submit_deliverable(self, job_id: str, deliverable_url: str) -> str:
        assert self._get(job_id, "status") == "in_progress", "Job is not in progress"
        assert len(deliverable_url) >= 10, "Deliverable URL is too short"

        self._set(job_id, "deliverable_url", deliverable_url)
        self._set(job_id, "status", "under_review")

        return f"Deliverable submitted for job {job_id}. Awaiting AI verification."

    @gl.public.write
    def verify_deliverable(self, job_id: str) -> str:
        assert self._get(job_id, "status") == "under_review", "Job is not under review"

        title = self._get(job_id, "title")
        description = self._get(job_id, "description")
        requirements = self._get(job_id, "requirements")
        deliverable_url = self._get(job_id, "deliverable_url")

        def leader_fn():
            web_data = ""
            try:
                response = gl.nondet.web.get(deliverable_url)
                raw = response.body.decode("utf-8")
                web_data = raw[:3000]
            except Exception:
                web_data = "Could not fetch deliverable content."

            prompt = f"""You are an impartial AI verifier for a freelancer marketplace.
Your job is to determine if the delivered work meets the job requirements.

Job Title: {title}

Job Description:
{description}

Requirements that must be met:
{requirements}

Deliverable content fetched from {deliverable_url}:
{web_data}

Based on the requirements and the deliverable content, decide if the work was completed.

Respond ONLY with this JSON:
{{"verdict": "APPROVED", "confidence": 80, "reasoning": "two sentences explaining if requirements were met"}}

verdict must be exactly APPROVED or REJECTED, confidence is 0 to 100,
reasoning explains which requirements were or were not met.
No extra text."""

            result = gl.nondet.exec_prompt(prompt)
            clean = result.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)

            verdict = data.get("verdict", "REJECTED")
            confidence = int(data.get("confidence", 50))
            reasoning = data.get("reasoning", "")

            if verdict not in ("APPROVED", "REJECTED"):
                verdict = "REJECTED"
            confidence = max(0, min(100, confidence))

            return json.dumps({
                "verdict": verdict,
                "confidence": confidence,
                "reasoning": reasoning
            }, sort_keys=True)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                validator_raw = leader_fn()
                leader_data = json.loads(leader_result.calldata)
                validator_data = json.loads(validator_raw)
                if leader_data["verdict"] != validator_data["verdict"]:
                    return False
                return abs(leader_data["confidence"] - validator_data["confidence"]) <= 15
            except Exception:
                return False

        raw = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        data = json.loads(raw)

        verdict = data["verdict"]
        confidence = data["confidence"]
        reasoning = data["reasoning"]

        if verdict == "APPROVED":
            self._set(job_id, "status", "completed")
        else:
            self._set(job_id, "status", "rejected")

        self._set(job_id, "verdict", verdict)
        self._set(job_id, "reasoning", reasoning)

        return (
            f"Job {job_id} verification complete. "
            f"Verdict: {verdict} ({confidence}% confidence). "
            f"{reasoning}"
        )

    @gl.public.write
    def resubmit_deliverable(self, job_id: str, new_deliverable_url: str) -> str:
        assert self._get(job_id, "status") == "rejected", "Job must be rejected to resubmit"
        assert len(new_deliverable_url) >= 10, "Deliverable URL is too short"

        self._set(job_id, "deliverable_url", new_deliverable_url)
        self._set(job_id, "status", "under_review")
        self._set(job_id, "verdict", "")
        self._set(job_id, "reasoning", "")

        return f"New deliverable submitted for job {job_id}. Awaiting re-verification."

    def _get(self, job_id: str, field: str) -> str:
        key = f"{job_id}_{field}:"
        for i in range(len(self.job_data)):
            if self.job_data[i].startswith(key):
                return self.job_data[i][len(key):]
        return ""

    def _set(self, job_id: str, field: str, value: str) -> None:
        key = f"{job_id}_{field}:"
        for i in range(len(self.job_data)):
            if self.job_data[i].startswith(key):
                self.job_data[i] = f"{key}{value}"
                return
        self.job_data.append(f"{key}{value}")
