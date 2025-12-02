 section captures the end-to-end testing conducted to validate communication flow, authentication behaviour, and functional correctness across the entire integration chain — from the upstream device, through Tyk API Gateway, to the backend API hosted behind the Application Load Balancer (ALB).
The objective was to ensure that all components work cohesively and that Tyk enforces the required authentication and routing logic.

⸻

1. Backend API Direct Validation (Baseline Test)

The first phase of testing focused on validating the backend API independently, without involving Tyk.
This helped confirm that the API was functional and responding correctly before introducing any gateway-level logic.

What was done:
	•	Executed curl requests directly against the Backend API ALB DNS.
	•	Verified that the API endpoints returned the expected responses.
	•	Confirmed that networking, security groups, and target group health checks were all functioning correctly.

Outcome:
Backend API was confirmed healthy and fully functional.
(This establishes a clean baseline for further tests.)

⸻

2. Tyk Gateway Integration Test (End-to-End Path Via Tyk)

After validating the backend API, we routed the same requests through Tyk Gateway to confirm end-to-end connectivity and authentication.

What was done:
	•	Executed curl requests against the Tyk Gateway ALB DNS.
	•	Included the required authentication token/header configured within Tyk.
	•	Observed traffic routing from:
Client → Tyk Gateway → API Definition → Upstream → Backend API (ALB → Target Group)
	•	Verified Tyk middle-layer responsibilities, including:
	•	Authentication
	•	Key validation
	•	Rate limiting / policy checks (where applicable)
	•	Upstream endpoint routing

Outcome:
End-to-end connectivity via Tyk worked successfully, with Tyk validating requests and forwarding them to the backend API with zero issues.
This confirmed that both routing and authentication were configured correctly.

⸻

3. Full Journey Test From the Device (Real Operational Flow)

The final validation replicated the real upstream flow where requests originate from the actual device/system.

What was done:
	•	Triggered the API flow from the upstream device/application.
	•	Confirmed that traffic travelled the full production-intended path:
Device → Upstream Layer → Tyk Gateway → Backend API
	•	Validated that:
	•	Authentication was handled by Tyk.
	•	Tyk forwarded requests to the backend API.
	•	Response returned all the way back to the device.
	•	Captured logs and screenshots to verify headers, timestamps, and response codes.

Outcome:
The entire request lifecycle — from device initiation to backend processing and response — worked as expected.
This confirmed that the integrated system functions correctly in a real-world invocation scenario.
