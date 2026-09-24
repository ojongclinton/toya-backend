# OTP-verified signup plan (Clients & Drivers)

Owner: Backend
Status: Draft (to be executed)
Date: 2026-01-05

## 1) Summary
Introduce phone-OTP verification for account signup for both Clients and Drivers. Registration will no longer issue JWT tokens immediately. Instead, the user receives an OTP by SMS, verifies the phone, and only then receives tokens. Logins will be denied until the phone number is verified.

This plan also removes OTP disclosure from API responses for password reset and adds tests to guard the core implementation.

## 2) Current state (as of today)
- Registration endpoints:
  - Clients: `clients/views.py::register_client` (POST `/api/clients/auth/register/`) issues tokens immediately and sends a welcome SMS.
  - Drivers: `drivers/views.py::register_drivers` (POST `/api/drivers/auth/register/`) issues tokens immediately and sends a welcome SMS.
- OTP implementation exists only for password reset (not signup):
  - Models: `core/models.py::PasswordResetCode`
  - Clients endpoints: `forgot_password`, `validate_reset_code_clients`, `reset_password`
  - Drivers endpoints: `forgot_password`, `validate_reset_code_drivers`, `reset_password`
- Security gap: `forgot_password` responses return the OTP in the JSON body (should be removed for production).

## 3) Objectives
- Enforce phone-OTP verification for new signups (Clients + Drivers) before issuing JWT tokens.
- Provide endpoints to request (resend) and verify signup OTP.
- Gate all logins on `is_phone_verified`.
- Remove OTP value from API responses.
- Provide comprehensive tests for the new signup flow and gating.

## 4) Non-goals (for this iteration)
- Email-based signup verification.
- Backoffice admin phone verification changes (admin continues as-is).
- Advanced rate limiting/throttling (we will scaffold and leave as optional follow-up).

## 5) Design decisions
- Add a boolean flag on `Clients` and `Drivers` models: `is_phone_verified = models.BooleanField(default=False)`.
  - We do NOT put it on `BaseUser` to avoid affecting Backoffice admins.
- Create a dedicated `SignupOTP` model to separate signup OTPs from password reset codes:
  - `user` (FK to `BaseUser`), `code` (CharField length 6), `created_at` (auto_now_add), `is_used` (bool, default False), `attempts` (SmallInteger, default 0).
  - TTL: 15 minutes (same policy as password reset OTPs) evaluated as `now() - created_at <= timedelta(minutes=15)`.
  - We use `update_or_create` to rotate the code on resend.
- OTP delivery: use existing Celery SMS task `clients.tasks.notifiy_new_user_with_sms_tasks`.
- Registration flow change: registration creates the user with `is_phone_verified=False`, generates OTP, sends SMS, returns a response stating verification is required (no tokens yet).
- Verification flow: verify endpoint checks OTP, marks `is_used=True`, sets the user’s `is_phone_verified=True`, and returns JWT tokens.
- Login gating: `login_client` / `login_drivers` return 403 (or 400) with a clear message if the user is not verified.
- Security: stop returning OTP values in any API response.

## 6) Data model changes
- `clients/models.py::Clients`:
  - Add `is_phone_verified = models.BooleanField(default=False)`.
- `drivers/models.py::Drivers`:
  - Add `is_phone_verified = models.BooleanField(default=False)`.
- `core/models.py`:
  - Add new model `SignupOTP` with fields:
    - `user = models.OneToOneField(BaseUser, on_delete=models.CASCADE)` (OneToOne ensures a single active code per user; we’ll rotate on resend)
    - `code = models.CharField(max_length=6)`
    - `created_at = models.DateTimeField(auto_now_add=True)`
    - `is_used = models.BooleanField(default=False)`
    - `attempts = models.PositiveSmallIntegerField(default=0)`

Migration plan: three migrations (core first, then clients, then drivers), or one combined migration set depending on ordering constraints.

## 7) API changes
- Modify existing register endpoints (breaking change by design):
  - Clients: `POST /api/clients/auth/register/`
    - Behavior: create user with `is_phone_verified=False`, generate/send OTP via SMS, return response without tokens:
      - `{ "Message": "Signup initiated. Please verify the code sent to your phone.", "Id": <user_id>, "verification_required": true }`
  - Drivers: `POST /api/drivers/auth/register/` (same behavior)

- Add new signup-OTP endpoints:
  - Clients:
    - `POST /api/clients/auth/request-signup-otp/` body `{ "phone_number": "+2376XXXXXXXX" }`
      - Re-generate (rotate) OTP for the existing unverified user and send via SMS.
    - `POST /api/clients/auth/verify-signup-otp/` body `{ "phone_number": "+2376XXXXXXXX", "otp_code": "123456" }`
      - Validate code (match + TTL + attempts), set `is_used=True`, set `is_phone_verified=True`, return JWT tokens.
  - Drivers: mirror the same two endpoints under `/api/drivers/auth/...`.

- Gate login endpoints:
  - Clients `POST /api/clients/auth/login/`
  - Drivers `POST /api/drivers/auth/login/`
  - If `is_phone_verified` is False, return 403 with: `{ "Message": "Phone number not verified. Please verify to continue." }`

- Remove OTP from responses:
  - `clients/views.py::forgot_password` and `drivers/views.py::forgot_password`: remove `"OTP": otp` from returned data.

- OpenAPI / drf-spectacular annotations: update request/response schemas accordingly.

## 8) Application flow (happy path)
1. Client or Driver submits register.
2. Backend creates user with `is_phone_verified=False`, generates OTP, sends SMS, returns registration-pending response.
3. User enters `{phone_number, otp_code}` to `verify-signup-otp`.
4. Backend validates OTP (code matches, not used, not expired), marks verified, returns JWT tokens.
5. User can now login (or if tokens already provided by verify, immediately authenticated).

## 9) Error handling
- Wrong code: 400 `{ "Message": "Invalid code." }` (+ increment attempts)
- Expired code: 400 `{ "Message": "Code expired." }`
- Already used: 400 `{ "Message": "This validation code has already been used." }`
- Too many attempts (e.g., attempts >= 5): 429 `{ "Message": "Too many invalid attempts. Please request a new code." }`

## 10) Security considerations
- Do not return OTP in responses.
- Limit OTP attempts per code (e.g., 5 attempts).
- **Throttling (required)**: Implement DRF throttling classes for OTP endpoints to prevent abuse:
  - `request-signup-otp`: 5 requests per hour per phone number.
  - `verify-signup-otp`: 10 requests per hour per phone number.
  - `forgot_password`: 3 requests per hour per phone number.
- Code length 6 numeric; generated via `random.randint` (sufficient for OTP; could consider `secrets` if desired).

## 10a) Rollback safety: feature flag approach
To avoid breaking changes and enable easy rollback:
- Add Django setting: `ENFORCE_PHONE_VERIFICATION = env.bool('ENFORCE_PHONE_VERIFICATION', default=False)`
- When `False` (default): 
  - Registration continues to issue tokens immediately (backward compatible)
  - Login does not check `is_phone_verified`
  - New endpoints are available but optional
- When `True`: enforces the new OTP flow.
- This allows gradual rollout: deploy with flag OFF, test in staging, then enable in production.
- Rollback: simply set env var to `False` and restart.

## 11) Testing plan (pytest + DRF APIClient)
Tests will be added for both Clients and Drivers:

- Unit tests for `SignupOTP` model logic:
  - Code generation and rotation with `update_or_create`.
  - TTL expiration check.
  - Attempts increment and lockout behavior.

- API tests for signup flow (happy path):
  - Register => returns verification_required true, no tokens.
  - Verify with correct code within TTL => returns tokens and sets `is_phone_verified=True`.
  - Login allowed after verification.

- API tests for negative cases:
  - Verify with wrong code => 400, attempts++.
  - Verify with expired code => 400.
  - Verify after attempts exceeded => 429.
  - Login before verification => 403.

- Regression tests:
  - Forgot password no longer returns OTP value.

Implementation details:
- Use pytest and DRF’s `APIClient`.
- Mock SMS sending (Celery task) to avoid external calls (e.g., monkeypatch `notifiy_new_user_with_sms_tasks.delay`).

## 12) Implementation steps (tracking)
- [ ] Add `is_phone_verified` to `Clients` and `Drivers` models, create migrations. (Task: models_flag)
- [ ] Create `core.models.SignupOTP` model + migration. (Task: model_signup_otp)
- [ ] Add `ENFORCE_PHONE_VERIFICATION` feature flag to settings with env var support.
- [ ] Update serializers if needed (read_only flags for `is_phone_verified`).
- [ ] Update registration views: conditionally create unverified users and send OTP based on flag. (Task: update_register_flow)
- [ ] Add endpoints: `request-signup-otp`, `verify-signup-otp` (clients/drivers). (Task: endpoints_signup_otp)
- [ ] Gate login on `is_phone_verified` (conditional on feature flag). (Task: gate_login)
- [ ] Remove OTP value from forgot_password responses. (Task: remove_otp_from_responses)
- [ ] **Implement throttling for OTP endpoints** (DRF throttling classes). (Task: throttling_otp)
- [ ] Tests: unit + API for both roles; mock SMS; add fixtures; test both flag states. (Task: tests_signup_otp)
- [ ] Update drf-spectacular annotations and README/API docs. (Task: update_api_docs)

## 13) Backward compatibility & rollout
- This is a breaking change for consumers expecting tokens on register.
- Coordinate with mobile apps to adopt the new flow:
  - After register, prompt for OTP input.
  - Provide resend option via `request-signup-otp`.
  - On verification success, store tokens and proceed.

## 14) Rollback plan
- Set `ENFORCE_PHONE_VERIFICATION=False` in environment variables and restart application.
- This immediately reverts to legacy behavior: register issues tokens, login doesn't check verification.
- No code changes or migrations need to be rolled back.
- If database corruption suspected, migrations can be reversed, but the feature flag makes this unnecessary.

## 15) Estimates
- Models/migrations: 1–2 hours
- Views/serializers/urls: 2–3 hours
- Tests: 2–3 hours
- Docs + polishing: 1 hour

Total: ~1 working day.
