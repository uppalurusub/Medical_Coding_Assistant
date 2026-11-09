# Medical Coding Assistant API

A FastAPI-based **Medical Coding Assistant** that uses an LLM with LangChain structured output to generate ICD-10 diagnosis-code and CPT procedure-code recommendations from clinical information.

> **Important:** This project is an AI-assisted coding prototype/reference implementation. It should not be treated as an authoritative medical-coding system without validation against current official coding references, payer rules, organizational policies, and qualified human review.

---

## 1. Overview

The application accepts:

- Diagnosis / clinical condition
- Procedure performed
- Optional clinical notes
- Desired response language
- User ID
- Session ID

It returns:

- ICD-10 code recommendations
- CPT code recommendations
- Code descriptions
- Per-code confidence scores
- Overall confidence score
- Coding notes
- Validation status

### Technology Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Validation | Pydantic |
| LLM orchestration | LangChain |
| LLM client | `langchain-openai` / OpenAI-compatible API |
| Model provider | Configured through environment variables; current code is compatible with OpenRouter-style endpoints |
| Structured output | LangChain `with_structured_output()` |
| Tool framework | LangChain `@tool` |
| Logging | Loguru |
| Experiment tracking | MLflow |
| Configuration | `python-dotenv` |
| Language | Python |

---

## 2. Current Architecture

```text
                    ┌──────────────────────────────┐
                    │          Client              │
                    │ Swagger / Postman / Frontend │
                    └──────────────┬───────────────┘
                                   │
                                   │ POST /api/v1/medical-coding
                                   ▼
                    ┌──────────────────────────────┐
                    │       FastAPI Router          │
                    │    coding_router.py          │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │      MedicalCodingService     │
                    │       coding_service.py       │
                    │                              │
                    │  • MLflow run                │
                    │  • execution timing          │
                    │  • request/response logging   │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   MedicalCodingImplementation │
                    │        coding_impl.py         │
                    │                              │
                    │  • Build prompt              │
                    │  • Invoke LLM                │
                    │  • Structured output          │
                    └──────────────┬───────────────┘
                                   │
                     ┌─────────────┴─────────────┐
                     ▼                           ▼
          ┌─────────────────────┐     ┌─────────────────────┐
          │ CodingPrompt        │     │ ChatOpenAI /        │
          │ coding_prompt.py    │     │ OpenAI-compatible   │
          └─────────────────────┘     │ LLM endpoint        │
                                      └──────────┬──────────┘
                                                 │
                                                 ▼
                                    ┌────────────────────────┐
                                    │ MedicalCodingResponse  │
                                    │ Pydantic structured    │
                                    │ output                 │
                                    └────────────────────────┘
```

---

## 3. Project Structure

```text
app/
├── agents/
│   └──                    # Currently empty
│
├── config/
│   └── llm_config.py      # LLM configuration and initialization
│
├── implementations/
│   └── coding_impl.py     # Core LLM-based coding implementation
│
├── memory/
│   └──                    # Currently empty
│
├── models/
│   ├── request_model.py   # API request schema
│   └── response_model.py  # API response schemas
│
├── prompts/
│   └── coding_prompt.py   # System/user prompt templates
│
├── routers/
│   └── coding_router.py   # FastAPI endpoint
│
├── services/
│   └── coding_service.py  # Service orchestration + MLflow
│
├── tools/
│   └── coding_tools.py    # Sample ICD-10/CPT lookup tools
│
├── utils/
│   └── logger.py          # Loguru configuration
│
└── main.py                # FastAPI application entry point
```

The uploaded project also contains Python `__pycache__` files. These are generated artifacts and normally should not be committed to source control.

---

## 4. API Endpoints

### Root

```http
GET /
```

Example response:

```json
{
  "application": "Medical Coding Assistant",
  "version": "1.0.0",
  "status": "RUNNING"
}
```

### Health Check

```http
GET /health
```

Example:

```json
{
  "status": "UP",
  "service": "Medical Coding Assistant API"
}
```

### Medical Coding

```http
POST /api/v1/medical-coding
```

The endpoint is implemented in:

```text
app/routers/coding_router.py
```

---

## 5. Request Schema

```json
{
  "diagnosis": "Type 2 diabetes mellitus with diabetic neuropathy",
  "procedure": "Comprehensive diabetic foot examination",
  "clinical_notes": "Patient complains of numbness and tingling in both feet.",
  "language": "English",
  "user_id": "USR001",
  "session_id": "SES001"
}
```

### Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `diagnosis` | string | Yes | Diagnosis or clinical condition |
| `procedure` | string | Yes | Procedure performed |
| `clinical_notes` | string | No | Additional clinical information |
| `language` | string | No | Response language; defaults to English |
| `user_id` | string | Yes | User identifier |
| `session_id` | string | Yes | Session identifier |

---

## 6. Response Schema

The response model is:

```text
MedicalCodingResponse
├── diagnosis
├── procedure
├── icd10_codes[]
│   ├── code
│   ├── description
│   └── confidence
├── cpt_codes[]
│   ├── code
│   ├── description
│   └── confidence
├── coding_notes
├── confidence_score
├── validation
│   ├── status
│   └── message
├── language
└── generated_by
```

Example:

```json
{
  "diagnosis": "Type 2 diabetes mellitus with diabetic neuropathy",
  "procedure": "Comprehensive diabetic foot examination",
  "icd10_codes": [
    {
      "code": "E11.40",
      "description": "Type 2 diabetes mellitus with diabetic neuropathy",
      "confidence": 0.96
    }
  ],
  "cpt_codes": [
    {
      "code": "2028F",
      "description": "Foot examination performed",
      "confidence": 0.90
    }
  ],
  "coding_notes": "Review the clinical documentation and applicable coding guidelines before final code assignment.",
  "confidence_score": 0.93,
  "validation": {
    "status": "VALID",
    "message": "Coding response generated successfully."
  },
  "language": "English",
  "generated_by": "Medical Coding Assistant"
}
```

The exact generated values are model-dependent and should not be assumed to be authoritative.

---

## 7. Processing Flow

```text
1. Client submits diagnosis + procedure + optional clinical notes
                         │
                         ▼
2. FastAPI validates request with Pydantic
                         │
                         ▼
3. Router calls MedicalCodingService
                         │
                         ▼
4. Service starts an MLflow run
                         │
                         ▼
5. MedicalCodingImplementation creates ChatPromptTemplate
                         │
                         ▼
6. System + user prompts are sent to the LLM
                         │
                         ▼
7. LLM response is constrained to MedicalCodingResponse
                         │
                         ▼
8. Structured response is returned to service
                         │
                         ▼
9. Execution time is recorded in MLflow
                         │
                         ▼
10. FastAPI returns JSON response
```

---

## 8. LLM Configuration

The current implementation loads configuration from `.env` using `python-dotenv`.

The code expects:

```env
fallback_model_1=YOUR_MODEL_NAME
openrouter_api_key=YOUR_API_KEY
base_url=YOUR_OPENAI_COMPATIBLE_BASE_URL
```

For an OpenRouter-compatible configuration, the base URL is typically an OpenAI-compatible chat-completions endpoint.

Do **not** commit API keys to Git.

A recommended `.env.example` is:

```env
fallback_model_1=your-model-name
openrouter_api_key=your-api-key
base_url=your-openai-compatible-base-url

MLFLOW_TRACKING_URI=http://localhost:5000
```

### Configuration improvement recommended

The current `coding_service.py` hard-codes:

```python
mlflow.set_tracking_uri("http://localhost:5000")
```

For production, move this to environment-based configuration.

---

## 9. Structured Output

The implementation uses:

```python
self.llm.with_structured_output(
    MedicalCodingResponse
)
```

This is an important design choice because it makes the LLM target a Pydantic schema rather than returning unconstrained text.

Conceptually:

```text
LLM
 │
 ├── diagnosis
 ├── procedure
 ├── ICD-10 codes
 ├── CPT codes
 ├── confidence
 ├── coding notes
 └── validation
       │
       ▼
Pydantic MedicalCodingResponse
```

This reduces malformed JSON responses, but it does **not** guarantee that the medical codes themselves are correct.

---

## 10. Tool Layer

`app/tools/coding_tools.py` defines three LangChain tools:

### `icd_lookup_tool`

Performs a simple keyword lookup against an in-memory dictionary.

Current sample entries include:

```text
diabetes
diabetic neuropathy
hypertension
asthma
```

### `cpt_lookup_tool`

Performs a simple keyword lookup against an in-memory CPT dictionary.

Current sample entries include:

```text
office visit
foot examination
blood pressure check
```

### `medical_coding_tool`

Combines the ICD and CPT lookup tools.

### Important implementation observation

The tools are currently **not active in the main LLM execution path**.

In `coding_impl.py`, the following tool-binding section is commented out:

```python
self.tools = [
    icd_lookup_tool,
    cpt_lookup_tool,
    medical_coding_tool
]

self.llm_with_tools = self.llm.bind_tools(
    self.tools
)
```

The active implementation therefore uses:

```text
Prompt → LLM → Structured Output
```

rather than:

```text
Prompt → Agent/LLM → ICD/CPT Tools → Evidence → Structured Output
```

This distinction is important when describing the application as a tool-augmented or agentic medical-coding system.

---

## 11. MLflow

The service attempts to track:

- Start time
- Input
- Response
- Endpoint
- Source
- End time
- Execution duration

Experiment:

```text
Medical_Coding_Assistant_Interface
```

Tracking URI currently defaults to:

```text
http://localhost:5000
```

Start MLflow separately, for example:

```bash
mlflow server --host 0.0.0.0 --port 5000
```

Then start the FastAPI application.

### Important MLflow consideration

The current implementation attempts to pass the Pydantic request and response objects directly to `mlflow.log_param()`:

```python
mlflow.log_param("input_text", request)
mlflow.log_param("response", response)
```

MLflow parameters should be serialized to supported primitive/string values. A safer pattern is:

```python
mlflow.log_param(
    "input_text",
    request.model_dump_json()
)

mlflow.log_param(
    "response",
    response.model_dump_json()
)
```

However, for healthcare applications, logging complete clinical input or model output to MLflow may expose PHI. Production implementations should apply data minimization, de-identification/redaction, access control, and retention policies.

---

## 12. Logging

Loguru is configured in:

```text
app/utils/logger.py
```

The application creates:

```text
logs/healthcare.log
logs/error.log
```

`main.py` additionally configures:

```text
logs/medical_coding.log
```

Logs are rotated and retained according to the configured policies.

### Production security consideration

Avoid logging:

- Patient identifiers
- Clinical notes
- PHI
- API keys
- Authorization tokens
- Full prompts containing sensitive data
- Full model responses containing sensitive data

The current service logs diagnosis and procedure values, so this should be reviewed before production healthcare deployment.

---

## 13. Installation

Create a virtual environment:

```bash
python -m venv .venv
```

Activate on Windows:

```bash
.venv\Scripts\activate
```

Activate on Linux/macOS:

```bash
source .venv/bin/activate
```

Install the required packages:

```bash
pip install fastapi uvicorn pydantic python-dotenv loguru mlflow langchain-core langchain-openai
```

---

## 14. Run the Application

From the project root:

```bash
uvicorn app.main:app --reload
```

The API should be available at:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

---

## 15. Example cURL

```bash
curl -X POST "http://localhost:8000/api/v1/medical-coding" \
  -H "Content-Type: application/json" \
  -d '{
    "diagnosis": "Type 2 diabetes mellitus with diabetic neuropathy",
    "procedure": "Comprehensive diabetic foot examination",
    "clinical_notes": "Patient complains of numbness and tingling in both feet.",
    "language": "English",
    "user_id": "USR001",
    "session_id": "SES001"
  }'
```

---

## 16. Architectural Strengths

### 16.1 Clear layered architecture

The project separates:

```text
Router
   ↓
Service
   ↓
Implementation
   ↓
Prompt / LLM
```

This is a good foundation for enterprise application development.

### 16.2 Pydantic contracts

Both request and response models are explicitly defined.

This improves:

- API validation
- Swagger documentation
- Type safety
- Structured LLM output
- Maintainability

### 16.3 Structured LLM response

Using `with_structured_output()` is preferable to manually parsing arbitrary JSON returned by an LLM.

### 16.4 Observability foundation

The project already includes:

- Loguru
- MLflow
- Execution timing
- Request/session identifiers
- Error handling

These provide a foundation for stronger LLMOps observability.

### 16.5 Tool abstraction

The ICD/CPT tools are already separated from the implementation layer, making it possible to replace the current dictionaries with:

- Coding databases
- REST APIs
- FHIR terminology services
- Vector search
- Knowledge graphs
- Enterprise coding services

---

## 17. Important Gaps / Risks

### 17.1 No authoritative coding knowledge source

The current ICD-10/CPT tool dictionaries are sample data.

For a real medical-coding system, code selection should be grounded in authoritative and current coding references.

Recommended architecture:

```text
Clinical Documentation
        │
        ▼
Terminology / Coding Retrieval
        │
        ├── ICD-10-CM
        ├── CPT
        ├── HCPCS
        ├── Payer rules
        └── Organizational policies
        │
        ▼
LLM reasoning
        │
        ▼
Coding validation
        │
        ▼
Human coder review
```

### 17.2 Tools are currently disconnected

The tool definitions exist, but `coding_impl.py` currently calls the LLM directly.

If tool augmentation is intended, enable and properly orchestrate the tools.

### 17.3 No explicit agent

The `agents/` directory is empty.

The current system is better described as:

```text
LLM-powered medical coding service
```

rather than a multi-agent medical coding system.

### 17.4 No memory implementation

The `memory/` directory is empty.

`session_id` is accepted by the API but is not currently used to retrieve or persist conversational memory.

If session memory is required, introduce a persistent store such as:

```text
PostgreSQL
Redis
MongoDB
```

or another approved enterprise data store.

### 17.5 No authentication / authorization

The request accepts `user_id`, but that is not equivalent to authentication.

A production API should implement:

```text
Authentication
      ↓
Identity
      ↓
RBAC / ABAC
      ↓
API authorization
      ↓
Audit logging
```

### 17.6 No explicit human-in-the-loop workflow

For ambiguous or high-risk coding, the system should support:

```text
AI recommendation
       ↓
Confidence / validation
       ↓
Review Required?
   ┌───┴────┐
  No       Yes
  │         │
  ▼         ▼
Return    Human Coder
            │
            ▼
       Approve / Modify
```

### 17.7 Confidence is model-generated

A confidence score generated by the LLM should not automatically be interpreted as a calibrated statistical probability.

For production use, confidence should ideally be supported by measurable evidence such as:

- Retrieval score
- Terminology match
- Coding-rule validation
- Model evaluation
- Historical accuracy
- Human reviewer agreement

### 17.8 Limited validation

The current `validation` object is generated as part of the LLM response. There is no independent deterministic coding validator after the LLM response.

A stronger design would be:

```text
LLM Candidate Codes
        ↓
Deterministic Validator
        ↓
Terminology Validation
        ↓
Rule Validation
        ↓
Payer/Policy Validation
        ↓
Final Recommendation
```

---

## 18. Recommended Enterprise Architecture

For a production-grade medical coding platform, consider evolving the application to:

```text
                         ┌──────────────────┐
                         │  Client / EHR    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ API Gateway      │
                         │ Auth / RBAC      │
                         └────────┬─────────┘
                                  │
                                  ▼
                       ┌──────────────────────┐
                       │ Coding Orchestrator  │
                       └──────────┬───────────┘
                                  │
             ┌────────────────────┼─────────────────────┐
             ▼                    ▼                     ▼
      ┌─────────────┐      ┌─────────────┐      ┌──────────────┐
      │ Clinical    │      │ Terminology  │      │ Coding Rules │
      │ Extraction  │      │ Retrieval    │      │ Validator    │
      └──────┬──────┘      └──────┬──────┘      └──────┬───────┘
             │                    │                     │
             └────────────────────┼─────────────────────┘
                                  ▼
                         ┌──────────────────┐
                         │ LLM / Agent      │
                         │ Reasoning        │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Validation       │
                         │ & Guardrails     │
                         └────────┬─────────┘
                                  │
                          ┌───────┴────────┐
                          ▼                ▼
                   ┌────────────┐   ┌─────────────┐
                   │ Auto Return│   │ Human Review│
                   └────────────┘   └──────┬──────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │ Audit Trail  │
                                    └──────────────┘
```

---

## 19. Suggested Future Modules

A scalable implementation could evolve toward:

```text
app/
├── agents/
│   ├── coding_orchestrator.py
│   ├── diagnosis_agent.py
│   ├── procedure_agent.py
│   ├── icd_agent.py
│   ├── cpt_agent.py
│   ├── validation_agent.py
│   └── review_agent.py
│
├── tools/
│   ├── icd_lookup.py
│   ├── cpt_lookup.py
│   ├── hcpcs_lookup.py
│   ├── terminology_search.py
│   └── coding_rules.py
│
├── guardrails/
│   ├── input_guardrail.py
│   ├── output_guardrail.py
│   ├── phi_guardrail.py
│   └── coding_guardrail.py
│
├── memory/
│   ├── repository.py
│   └── session_memory.py
│
├── observability/
│   ├── metrics.py
│   ├── tracing.py
│   └── llm_telemetry.py
│
└── security/
    ├── authentication.py
    ├── authorization.py
    ├── rbac.py
    └── audit.py
```

---

## 20. Testing Strategy

Recommended test layers:

### Unit Tests

Test:

- Request validation
- Response validation
- Prompt construction
- ICD lookup
- CPT lookup
- Coding validation
- Error handling

### Integration Tests

Test:

```text
FastAPI
   ↓
Service
   ↓
Implementation
   ↓
LLM
   ↓
Structured Response
```

### Evaluation Tests

Build a labeled coding dataset containing:

```text
Clinical documentation
Expected ICD-10
Expected CPT
Coding rationale
Reviewer decision
```

Measure:

- Exact code accuracy
- Top-k accuracy
- Precision
- Recall
- F1
- Human agreement
- Invalid-code rate
- Unsupported-code rate
- Review-required rate

### LLM Evaluation

Also evaluate:

- Hallucination rate
- Evidence grounding
- Structured-output validity
- Confidence calibration
- Prompt robustness
- Coding guideline adherence

---

## 21. Production Readiness Checklist

### API

- [ ] Authentication
- [ ] Authorization
- [ ] Rate limiting
- [ ] Request correlation ID
- [ ] Standard error schema
- [ ] API versioning

### Healthcare / Privacy

- [ ] PHI classification
- [ ] PHI redaction
- [ ] Encryption in transit
- [ ] Encryption at rest
- [ ] Audit trail
- [ ] Data retention policy
- [ ] Access controls
- [ ] Environment-specific secrets

### AI

- [ ] Authoritative coding retrieval
- [ ] Tool calling
- [ ] Deterministic validation
- [ ] Guardrails
- [ ] Human review
- [ ] Evaluation dataset
- [ ] Confidence calibration
- [ ] Prompt/version management

### Observability

- [ ] MLflow
- [ ] LLM tracing
- [ ] Latency metrics
- [ ] Token metrics
- [ ] Error metrics
- [ ] Tool-call metrics
- [ ] Model performance monitoring

### Deployment

- [ ] Dockerfile
- [ ] Docker Compose
- [ ] Kubernetes manifests
- [ ] Health/readiness probes
- [ ] Secrets management
- [ ] CI/CD pipeline

---

## 22. Overall Assessment

This repository provides a **good foundational prototype for an LLM-powered medical coding API**.

The strongest aspects are:

1. Clear Router → Service → Implementation separation.
2. Pydantic request/response contracts.
3. LangChain structured output.
4. Separate prompt and tool modules.
5. Loguru-based application logging.
6. MLflow instrumentation.
7. FastAPI/OpenAPI documentation support.

The main architectural limitation is that the current implementation is **LLM-centric rather than truly tool-grounded or agentic**:

```text
Current:
Request
  → Prompt
  → LLM
  → Structured Response

Target:
Request
  → Clinical Extraction
  → Authoritative Coding Retrieval
  → Agent/LLM Reasoning
  → Deterministic Validation
  → Guardrails
  → Human Review when required
  → Auditable Final Recommendation
```

For a healthcare production environment, the most important next step is to replace the sample in-memory code dictionaries and model-only validation with **authoritative terminology retrieval + deterministic coding validation + human review + privacy/security controls**.

---

## 23. Quick Start

```bash
# 1. Create environment
python -m venv .venv

# 2. Activate
.venv\Scripts\activate

# 3. Install dependencies
pip install fastapi uvicorn pydantic python-dotenv loguru mlflow langchain-core langchain-openai

# 4. Configure environment variables
# Create .env with the required LLM settings

# 5. Start MLflow if required
mlflow server --host 0.0.0.0 --port 5000

# 6. Start API
uvicorn app.main:app --reload

# 7. Open Swagger
# http://localhost:8000/docs
```

---

## 24. License

No license file is included in the supplied project archive. Add an appropriate license before distributing the project.
