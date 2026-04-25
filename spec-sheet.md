# UPDATED SPEC SHEET: Reconciliation Agent + LC Doc Agent with Enhanced Tests & HITL
## Complete Test Coverage, Variance Analysis, Fraud Detection, Anomaly Detection, Enhanced UI/Backend

---

## PROJECT OVERVIEW (UPDATED)

**Goal:** Build production-ready agentic AI system with comprehensive test coverage:
1. **Reconciliation Agent** - 3-way match with detailed variance calculations, fraud detection, anomaly detection
2. **LC Doc Agent** - Letter of Credit validation (UCP 600 compliance checks)
3. **Guardrails** - All 5 guardrails with full HITL workflow
4. **Test Suite** - 15+ test scenarios covering all edge cases

**Tech Stack:**
- Backend: Python 3.8+
- LLM: OpenAI GPT-4o (via `openai` package)
- Vector DB: ChromaDB (for LC document embeddings)
- Audit DB: SQLite3 (for immutable decision logs)
- Frontend: Streamlit (with enhanced HITL UI)
- Testing: Pytest (unit + integration tests)

**Deliverables:**
- 8 Python core files + 1 test file
- 15 mock test data files
- Enhanced Streamlit app with detailed variance visualization
- Complete HITL approval workflow with side-by-side comparison

---

## ENHANCED FILE STRUCTURE

```
reconciliation-doc-agent/
├── .env                          # API keys (user creates)
├── .env.example                  # Template
├── requirements.txt              # Dependencies
├── README.md                     # Setup + usage
├── run_tests.py                  # Test runner (runs all scenarios)
│
├── # CORE BACKEND FILES
├── app.py                        # Streamlit main app
├── database.py                   # ChromaDB + SQLite management
├── guardrails.py                 # 5 guardrails + HITL helpers
├── reconciliation_agent.py       # 3-way match + fraud + anomaly detection
├── doc_agent.py                  # LC validation
│
├── # TEST & MOCK DATA
├── tests/
│   ├── __init__.py
│   ├── test_reconciliation_scenarios.py    # 15 test scenarios
│   ├── test_fraud_detection.py             # Fraud signal tests
│   ├── test_anomaly_detection.py           # Anomaly tests
│   ├── test_variance_calculations.py       # Variance formula tests
│   ├── test_guardrails.py                  # Guardrail tests
│   └── test_doc_agent.py                   # LC validation tests
│
├── test_data/
│   ├── # RECONCILIATION SCENARIOS (15 scenarios)
│   ├── scenario_01_perfect_match.json
│   ├── scenario_02_minor_qty_variance.json
│   ├── scenario_03_minor_price_variance.json
│   ├── scenario_04_qty_price_variance_combined.json
│   ├── scenario_05_major_qty_variance.json
│   ├── scenario_06_major_price_variance.json
│   ├── scenario_07_qty_mismatch_contract_invoice.json
│   ├── scenario_08_qty_mismatch_invoice_receipt.json
│   ├── scenario_09_fraud_signal_extra_qty_low_price.json
│   ├── scenario_10_fraud_signal_suspicious_timeline.json
│   ├── scenario_11_timeline_gap.json
│   ├── scenario_12_late_invoice.json
│   ├── scenario_13_multiple_anomalies.json
│   ├── scenario_14_edge_case_boundary.json
│   ├── scenario_15_extreme_variance.json
│   │
│   ├── # LC VALIDATION SCENARIOS (5 scenarios)
│   ├── lc_scenario_01_compliant.json
│   ├── lc_scenario_02_amount_mismatch.json
│   ├── lc_scenario_03_expiry_warning.json
│   ├── lc_scenario_04_compliance_violation.json
│   └── lc_scenario_05_edge_case.json
│
├── chroma_db/                    # ChromaDB vector store (auto-created)
├── audit_logs.db                 # SQLite audit trail (auto-created)
└── temp/                         # Temporary files (auto-created)
```

---

## DEPENDENCIES (requirements.txt)

```txt
streamlit==1.32.0
openai==1.12.0
chromadb==0.4.22
pandas==2.1.4
python-dotenv==1.0.0
pytest==7.4.3
pytest-cov==4.1.0
```

---

## ENHANCED: reconciliation_agent.py

### **DETAILED VARIANCE CALCULATION MODULE**

```python
class VarianceCalculator:
    """
    Calculate variance between documents with detailed breakdown.
    """
    
    def calculate_qty_variance(self, contract_qty: float, invoice_qty: float, receipt_qty: float) -> dict:
        """
        Calculate quantity variance percentages with three dimensions.
        
        Returns:
        {
            "contract_qty": float,
            "invoice_qty": float,
            "receipt_qty": float,
            "variance_contract_to_invoice_pct": float,      # (invoice - contract) / contract * 100
            "variance_invoice_to_receipt_pct": float,       # (receipt - invoice) / invoice * 100
            "variance_contract_to_receipt_pct": float,      # (receipt - contract) / contract * 100
            "qty_matches": {
                "contract_vs_invoice": bool,                # Within 0.5% threshold?
                "invoice_vs_receipt": bool,
                "contract_vs_receipt": bool
            },
            "severity": "GREEN|YELLOW|RED",
            "variance_classification": {
                "contract_to_invoice": "PERFECT|MINOR|MAJOR",
                "invoice_to_receipt": "PERFECT|MINOR|MAJOR",
                "contract_to_receipt": "PERFECT|MINOR|MAJOR"
            }
        }
        """
        
    def calculate_price_variance(self, contract_price: float, invoice_price: float) -> dict:
        """
        Calculate price variance with detailed breakdown.
        
        Returns:
        {
            "contract_price": float,
            "invoice_price": float,
            "variance_pct": float,                          # (invoice - contract) / contract * 100
            "variance_amount": float,                       # invoice - contract
            "price_match": bool,
            "direction": "INCREASE|DECREASE|NEUTRAL",       # Price went up, down, or same?
            "severity": "GREEN|YELLOW|RED"
        }
        """
        
    def calculate_timeline_variance(self, receipt_date: str, invoice_date: str) -> dict:
        """
        Calculate timeline variance.
        
        Returns:
        {
            "receipt_date": str,
            "invoice_date": str,
            "days_diff": int,                               # Days between receipt and invoice
            "timeline_status": "NORMAL|LATE|VERY_LATE",
            "severity": "GREEN|YELLOW|RED"
        }
        """
        
    def classify_variance_severity(self, variance_pct: float) -> tuple[str, int]:
        """
        Classify variance severity and return penalty.
        
        Rules:
        - < 0.5%: GREEN (0 penalty)
        - 0.5% to 2%: YELLOW (-15 penalty)
        - 2% to 5%: ORANGE (-25 penalty)
        - > 5%: RED (-40 penalty)
        
        Returns: (severity: str, confidence_penalty: int)
        """
```

### **FRAUD DETECTION MODULE**

```python
class FraudDetector:
    """
    Detect fraud signals through pattern recognition and anomaly detection.
    """
    
    def detect_fraud_signals(self, contract: dict, invoice: dict, receipt: dict) -> list:
        """
        Detect multiple fraud signals in one pass.
        
        Returns list of fraud signals detected:
        [
            {
                "signal_type": str,
                "severity": "LOW|MEDIUM|HIGH|CRITICAL",
                "message": str,
                "confidence_penalty": int,
                "financial_exposure_usd": float,
                "pattern": str,
                "recommendation": str
            }
        ]
        """
    
    def detect_qty_overstatement(self, contract_qty: float, invoice_qty: float, receipt_qty: float) -> dict:
        """
        Detect if invoice overstates quantity relative to receipt.
        
        Red flags:
        - Invoice qty > receipt qty (seller added extra, not received)
        - Invoice qty > contract qty + 5% (beyond agreed limit)
        - Discrepancy suggests added goods not ordered
        
        Returns:
        {
            "detected": bool,
            "signal_name": "QTY_OVERSTATEMENT",
            "severity": "CRITICAL" if detected else None,
            "qty_added": float,
            "pct_added": float,
            "financial_impact": float,
            "penalty": -50 if detected else 0,
            "reason": str
        }
        """
    
    def detect_price_manipulation(self, contract_price: float, invoice_price: float, contract_qty: float, invoice_qty: float) -> dict:
        """
        Detect suspicious price changes (especially with qty changes).
        
        Red flags:
        - Price drops significantly while qty increases (suspicious combo)
        - Price reduced > 5% without qty reduction
        - Price increase without justification
        
        FRAUD_PATTERN_1: Price ↓ + Qty ↑ (seller reduces price to hide extra qty)
        FRAUD_PATTERN_2: Price ↓↓ + Qty ↔ (significant price drop with same qty = suspicious)
        
        Returns:
        {
            "detected": bool,
            "signal_name": "PRICE_MANIPULATION" | "SUSPICIOUS_PRICE_QTY_COMBO",
            "severity": "CRITICAL" if combined with qty issue else "HIGH",
            "price_variance_pct": float,
            "qty_variance_pct": float,
            "pattern": "PRICE_DOWN_QTY_UP" | "PRICE_DOWN_ONLY" | etc,
            "financial_impact": float,
            "penalty": int,
            "confidence": float (0-1, how confident is this fraud?)
        }
        """
    
    def detect_timeline_manipulation(self, contract_date: str, receipt_date: str, invoice_date: str) -> dict:
        """
        Detect suspicious timeline patterns.
        
        Red flags:
        - Invoice dated BEFORE receipt (impossible in normal trade)
        - Invoice > 30 days after receipt (unusual delay)
        - Receipt > 30 days after contract (shipment took too long)
        
        Returns:
        {
            "detected": bool,
            "signal_name": "TIMELINE_MANIPULATION" | "INVOICE_BEFORE_RECEIPT" | "UNUSUAL_DELAY",
            "severity": "CRITICAL" if impossible else "HIGH",
            "issue": str,
            "contract_to_receipt_days": int,
            "receipt_to_invoice_days": int,
            "penalty": int,
            "recommendation": str
        }
        """
    
    def detect_duplicate_invoice(self, invoice_id: str, past_invoices: list) -> dict:
        """
        Detect if invoice has been seen before (duplicate submission fraud).
        
        Returns:
        {
            "detected": bool,
            "signal_name": "DUPLICATE_INVOICE",
            "severity": "CRITICAL" if detected,
            "previous_invoice_id": str,
            "previous_date": str,
            "financial_impact": float,
            "penalty": -100 if detected
        }
        """
    
    def calculate_overall_fraud_score(self, fraud_signals: list) -> dict:
        """
        Calculate composite fraud score (0-100, where 100 = definitely fraudulent).
        
        Returns:
        {
            "fraud_score": float (0-100),
            "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
            "total_signals_detected": int,
            "critical_count": int,
            "high_count": int,
            "recommendation": "APPROVE|INVESTIGATE|ESCALATE|REJECT"
        }
        """
```

### **ANOMALY DETECTION MODULE**

```python
class AnomalyDetector:
    """
    Detect statistical and logical anomalies.
    """
    
    def detect_all_anomalies(self, contract: dict, invoice: dict, receipt: dict) -> list:
        """
        Run all anomaly checks in one call.
        
        Returns list of detected anomalies.
        """
    
    def detect_qty_mismatch_patterns(self, contract_qty: float, invoice_qty: float, receipt_qty: float) -> list:
        """
        Detect various qty mismatch patterns.
        
        Patterns:
        1. INVOICE_QTY_NOT_IN_RECEIPT: Invoice qty ≠ receipt qty (items counted differently?)
        2. CONTRACT_INVOICE_MISMATCH: Contract qty ≠ invoice qty (order changed without approval?)
        3. CIRCULAR_MISMATCH: contract=100, invoice=102, receipt=98 (money-go-round)
        4. ZERO_DISCREPANCY: All three different (very suspicious)
        
        Returns:
        [
            {
                "anomaly_type": str,
                "pattern": str,
                "description": str,
                "severity": "LOW|MEDIUM|HIGH",
                "confidence": float (0-1),
                "penalty": int
            }
        ]
        """
    
    def detect_price_anomalies(self, contract_price: float, invoice_price: float, contract_qty: float) -> list:
        """
        Detect price-related anomalies.
        
        Anomalies:
        1. UNIT_PRICE_CHANGED: Per-unit price differs from contract
        2. PRICE_TOO_LOW: Price < 70% of contract (possible counterfeit goods?)
        3. PRICE_TOO_HIGH: Price > 130% of contract (overcharging?)
        4. ZERO_PRICE: Invoice price = 0 (impossible in real trade)
        
        Returns: List of anomalies
        """
    
    def detect_logical_inconsistencies(self, contract: dict, invoice: dict, receipt: dict) -> list:
        """
        Detect logical inconsistencies that don't fit together.
        
        Checks:
        1. If invoice qty > contract qty, but receipt qty < contract qty (doesn't add up)
        2. If price reduced + qty increased (why would seller do this?)
        3. If timeline impossible (invoice before receipt, etc.)
        4. If amounts don't reconcile mathematically
        
        Returns: List of inconsistencies
        """
    
    def detect_statistical_outliers(self, current_reconciliation: dict, historical_data: list) -> list:
        """
        Compare current reconciliation to historical patterns.
        
        (Future feature, for now return empty list)
        
        When implemented:
        - Compare variance to average variance in history
        - Flag if current variance is > 3 sigma from mean
        - Flag if pattern is completely new (never seen before)
        
        Returns: List of outlier anomalies
        """
```

### **ENHANCED reconcile() Function**

```python
def reconcile(self, contract: dict, invoice: dict, receipt: dict) -> dict:
    """
    Perform comprehensive 3-way reconciliation with variance + fraud + anomaly detection.
    
    FLOW:
    1. Calculate variance (qty, price, timeline) → detailed breakdown
    2. Detect fraud signals → fraud_score + recommendation
    3. Detect anomalies → list of patterns detected
    4. Run compliance checks
    5. Calculate confidence score with penalties
    6. Determine routing and HITL requirements
    7. Log decision with full forensic data
    
    Returns:
    {
        "audit_id": str,
        "status": str,                                      # AUTO_APPROVE | ROUTE_TO_SPECIALIST | ESCALATE_TO_MANAGER | ESCALATE_TO_DIRECTOR | REJECTED
        "confidence": int (0-100),
        
        # DETAILED VARIANCE ANALYSIS
        "variance_analysis": {
            "qty_variance": {
                "contract_qty": float,
                "invoice_qty": float,
                "receipt_qty": float,
                "variance_contract_to_invoice_pct": float,
                "variance_invoice_to_receipt_pct": float,
                "variance_contract_to_receipt_pct": float,
                "severity": "GREEN|YELLOW|RED|ORANGE"
            },
            "price_variance": {
                "contract_price": float,
                "invoice_price": float,
                "variance_pct": float,
                "variance_amount": float,
                "direction": "INCREASE|DECREASE|NEUTRAL",
                "severity": "GREEN|YELLOW|RED"
            },
            "timeline_variance": {
                "receipt_date": str,
                "invoice_date": str,
                "days_diff": int,
                "severity": "GREEN|YELLOW|RED"
            }
        },
        
        # FRAUD DETECTION
        "fraud_analysis": {
            "fraud_score": float (0-100),                  # 0 = safe, 100 = definitely fraud
            "risk_level": str,                             # LOW|MEDIUM|HIGH|CRITICAL
            "signals_detected": [
                {
                    "signal_type": str,
                    "severity": str,
                    "message": str,
                    "financial_exposure_usd": float,
                    "penalty": int
                }
            ],
            "total_financial_exposure": float
        },
        
        # ANOMALY DETECTION
        "anomaly_analysis": {
            "anomalies_detected": [
                {
                    "anomaly_type": str,
                    "pattern": str,
                    "description": str,
                    "severity": "LOW|MEDIUM|HIGH",
                    "confidence": float,
                    "penalty": int
                }
            ],
            "total_anomalies": int,
            "critical_anomalies": int
        },
        
        # COMPLIANCE & CONFIDENCE
        "compliance_check": dict,
        "confidence_breakdown": {
            "initial_confidence": 100,
            "qty_variance_penalty": int,
            "price_variance_penalty": int,
            "timeline_penalty": int,
            "fraud_penalty": int,
            "anomaly_penalty": int,
            "final_confidence": int
        },
        
        # ROUTING & HITL
        "routing": {
            "action": str,
            "owner": str,
            "deadline": str,
            "urgency": str,
            "requires_hitl": bool                          # Does human need to approve?
        },
        
        # DECISION METADATA
        "reasoning": str,                                  # Detailed explanation of decision
        "financial_impact": float,                         # ₹ or $ amount at risk
        "recommendation": str,                             # What action to take
        "created_at": str,
        "audit_id": str
    }
    """
```

---

## ENHANCED: guardrails.py

### **ENHANCED HITL WORKFLOW**

```python
class HITLWorkflow:
    """
    Complete human-in-the-loop approval workflow with detailed UI hints.
    """
    
    def create_hitl_display_data(self, agent_recommendation: dict) -> dict:
        """
        Create data structure optimized for HITL UI display.
        
        Returns:
        {
            "audit_id": str,
            "agent_recommendation": {
                "status": str,
                "confidence": int,
                "confidence_bar": str (for UI progress bar)
            },
            
            # SIDE-BY-SIDE COMPARISON (for UI table)
            "comparison_table": {
                "headers": ["Field", "Contract", "Invoice", "Receipt", "Status"],
                "rows": [
                    {
                        "field": "Quantity (MT)",
                        "contract": "100",
                        "invoice": "102",
                        "receipt": "100",
                        "status": "⚠️ WARNING",
                        "variance": "+2%"
                    },
                    # ... more rows
                ]
            },
            
            # VARIANCE VISUALIZATION DATA
            "variance_summary": {
                "qty_variance_pct": float,
                "price_variance_pct": float,
                "timeline_days": int,
                "variance_severity": "GREEN|YELLOW|RED"
            },
            
            # FRAUD & ANOMALY SUMMARY
            "risk_summary": {
                "fraud_score": int (0-100),
                "fraud_level_display": "🟢 LOW | 🟡 MEDIUM | 🟠 HIGH | 🔴 CRITICAL",
                "anomalies_count": int,
                "total_signals": int
            },
            
            # DETAILED ISSUES TO REVIEW
            "issues_for_review": [
                {
                    "issue_title": str,
                    "issue_description": str,
                    "severity": str,
                    "impact": str,
                    "requires_action": bool,
                    "suggested_action": str
                }
            ],
            
            # APPROVAL GUIDANCE
            "approval_guidance": {
                "decision_options": ["APPROVE", "REJECT", "REQUEST_MORE_INFO", "ESCALATE"],
                "recommended_action": str,
                "if_approve": str,                         # "Shipment will proceed to payment"
                "if_reject": str,                          # "Shipment will be escalated"
                "if_request_info": str,                    # "What specific info needed?"
                "escalation_reason": str (if needed)
            }
        }
        """
    
    def process_human_decision(self, audit_id: str, human_decision: str, human_notes: str, human_confidence: int) -> dict:
        """
        Process human's decision and calculate final status.
        
        Args:
            audit_id: Unique decision ID
            human_decision: "APPROVE" | "REJECT" | "REQUEST_MORE_INFO"
            human_notes: Human's justification
            human_confidence: 0-100, how confident is human?
        
        Returns:
        {
            "audit_id": str,
            "agent_recommendation": str,
            "human_decision": str,
            "human_notes": str,
            "human_confidence": int,
            "final_status": "APPROVED|REJECTED|PENDING_INFO",
            "override_reason": str (if human disagreed with agent),
            "final_confidence": int (blend of agent + human confidence),
            "approval_chain": [
                {
                    "timestamp": str,
                    "actor": "AGENT" | "HUMAN",
                    "decision": str,
                    "confidence": int
                }
            ],
            "logged_at": str
        }
        """
    
    def calculate_blended_confidence(self, agent_confidence: int, human_confidence: int, agreement: bool) -> int:
        """
        Blend agent and human confidence scores.
        
        Logic:
        - If agent and human agree: blend = 0.7 * agent + 0.3 * human (agent-heavy)
        - If human overrides agent approval: blend = 0.5 * agent + 0.5 * human (equal)
        - If human overrides agent rejection: blend = 0.3 * agent + 0.7 * human (human-heavy, they know something)
        
        Returns: int (final confidence 0-100)
        """
    
    def generate_approval_summary(self, decision_record: dict) -> str:
        """
        Generate human-readable summary of decision for record.
        
        Example output:
        "Agent recommended ROUTE_TO_SPECIALIST (78% confidence) due to:
         - Invoice qty 2% higher than receipt
         - Price variance within tolerance
         - 1 anomaly detected: unusual timeline
         
         Human APPROVED (92% confidence) after reviewing:
         - Confirmed with sales team this is authorized goodwill shipment
         - Price reduction justified by bulk order
         - Proceeding to payment
         
         Final Status: APPROVED (85% blended confidence)"
        
        Returns: str (formatted summary)
        """
```

---

## NEW: test_reconciliation_scenarios.py

### **15 COMPREHENSIVE TEST SCENARIOS**

```python
"""
15 test scenarios covering all 3-way match, fraud, and anomaly patterns.
"""

TEST_SCENARIOS = {
    # PERFECT MATCHES (Baseline)
    "scenario_01_perfect_match": {
        "description": "All three documents match perfectly",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected_output": {
            "status": "AUTO_APPROVE",
            "confidence": 100,
            "variance_severity": "GREEN",
            "fraud_score": 0,
            "anomalies_count": 0
        }
    },
    
    # MINOR VARIANCES (Acceptable)
    "scenario_02_minor_qty_variance": {
        "description": "Qty variance 0.5-2% (acceptable tolerance)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 101, "price_usd": 500, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100.5, "date": "2024-04-10"},
        "expected_output": {
            "status": "ROUTE_TO_SPECIALIST",
            "confidence": 85,                              # -15 for minor warning
            "variance_severity": "YELLOW",
            "fraud_score": 10,
            "anomalies_count": 0
        }
    },
    
    "scenario_03_minor_price_variance": {
        "description": "Price variance 0.5-1% (acceptable)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 100, "price_usd": 504, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected_output": {
            "status": "ROUTE_TO_SPECIALIST",
            "confidence": 85,
            "variance_severity": "YELLOW",
            "fraud_score": 10,
            "anomalies_count": 0
        }
    },
    
    "scenario_04_qty_price_variance_combined": {
        "description": "Both qty and price have minor variance together",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 101, "price_usd": 504, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100.5, "date": "2024-04-10"},
        "expected_output": {
            "status": "ROUTE_TO_SPECIALIST",
            "confidence": 75,                              # Multiple penalties stack
            "variance_severity": "YELLOW",
            "fraud_score": 15
        }
    },
    
    # MAJOR VARIANCES (Requires Review)
    "scenario_05_major_qty_variance": {
        "description": "Qty variance 2-5% (major, needs review)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 105, "price_usd": 500, "date": "2024-04-15"},
        "receipt": {"qty_mt": 103, "date": "2024-04-10"},
        "expected_output": {
            "status": "ESCALATE_TO_MANAGER",
            "confidence": 60,                              # -40 for major variance
            "variance_severity": "ORANGE",
            "fraud_score": 25,
            "anomalies_count": 1
        }
    },
    
    "scenario_06_major_price_variance": {
        "description": "Price variance > 2% (major)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 100, "price_usd": 512, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected_output": {
            "status": "ESCALATE_TO_MANAGER",
            "confidence": 60,
            "variance_severity": "RED",
            "fraud_score": 20
        }
    },
    
    # MISMATCHES (Critical)
    "scenario_07_qty_mismatch_contract_invoice": {
        "description": "Contract qty ≠ Invoice qty (order changed?)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 120, "price_usd": 500, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected_output": {
            "status": "ESCALATE_TO_MANAGER",
            "confidence": 50,
            "variance_severity": "RED",
            "fraud_score": 40,
            "anomalies_count": 2,
            "anomaly_types": ["QTY_MISMATCH_CONTRACT_INVOICE", "QTY_INCREASE"]
        }
    },
    
    "scenario_08_qty_mismatch_invoice_receipt": {
        "description": "Invoice qty ≠ Receipt qty (seller added extra?)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 110, "price_usd": 500, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected_output": {
            "status": "ESCALATE_TO_MANAGER",
            "confidence": 45,
            "variance_severity": "RED",
            "fraud_score": 50,                             # Higher fraud score (invoice claims extra items)
            "anomalies_count": 2,
            "anomaly_types": ["INVOICE_QTY_NOT_IN_RECEIPT", "QTY_OVERSTATEMENT"]
        }
    },
    
    # FRAUD SIGNALS (Most Critical)
    "scenario_09_fraud_signal_extra_qty_low_price": {
        "description": "FRAUD PATTERN: Extra qty + lower price (classic fraud signal)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 115, "price_usd": 450, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected_output": {
            "status": "ESCALATE_TO_DIRECTOR",                # Highest escalation
            "confidence": 30,
            "variance_severity": "RED",
            "fraud_score": 85,                             # Very high fraud score
            "fraud_signals": ["PRICE_DOWN_QTY_UP", "SUSPICIOUS_PRICE_QTY_COMBO"],
            "financial_exposure_usd": 5750,                # (15 MT × $450) - (100 MT × $500) = fraud amount
            "recommendation": "ESCALATE_FOR_INVESTIGATION"
        }
    },
    
    "scenario_10_fraud_signal_suspicious_timeline": {
        "description": "FRAUD PATTERN: Invoice before receipt (impossible timeline)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-05"},  # 5 days before receipt
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected_output": {
            "status": "ESCALATE_TO_DIRECTOR",
            "confidence": 20,
            "fraud_score": 95,                             # Critical fraud (impossible date)
            "fraud_signals": ["INVOICE_BEFORE_RECEIPT"],
            "anomalies_count": 1,
            "recommendation": "REJECT - IMPOSSIBLE TIMELINE"
        }
    },
    
    # TIMELINE ISSUES
    "scenario_11_timeline_gap": {
        "description": "Receipt > 10 days after invoice (unusual delay)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-05"},
        "receipt": {"qty_mt": 100, "date": "2024-04-20"},  # 15 days later
        "expected_output": {
            "status": "ROUTE_TO_SPECIALIST",
            "confidence": 70,
            "variance_severity": "YELLOW",
            "fraud_score": 35,
            "anomalies_count": 1,
            "anomaly_types": ["UNUSUAL_DELAY"]
        }
    },
    
    "scenario_12_late_invoice": {
        "description": "Invoice submitted 25 days after receipt",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 100, "price_usd": 500, "date": "2024-05-05"},  # 25 days late
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected_output": {
            "status": "ROUTE_TO_SPECIALIST",
            "confidence": 65,
            "fraud_score": 40,
            "anomalies_count": 1,
            "anomaly_types": ["INVOICE_DELAY", "PAYMENT_TIME_IMPACT"]
        }
    },
    
    # MULTIPLE ANOMALIES
    "scenario_13_multiple_anomalies": {
        "description": "3+ anomalies detected together (very suspicious)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 115, "price_usd": 480, "date": "2024-03-28"},  # Before receipt!
        "receipt": {"qty_mt": 95, "date": "2024-04-10"},
        "expected_output": {
            "status": "ESCALATE_TO_DIRECTOR",
            "confidence": 25,
            "fraud_score": 90,                             # Very high
            "anomalies_count": 5,
            "anomaly_types": [
                "INVOICE_BEFORE_RECEIPT",
                "QTY_OVERSTATEMENT",
                "QTY_MISMATCH_CONTRACT_INVOICE",
                "QTY_MISMATCH_INVOICE_RECEIPT",
                "CIRCULAR_MISMATCH"
            ],
            "recommendation": "REJECT - MULTIPLE CRITICAL ISSUES"
        }
    },
    
    # EDGE CASES
    "scenario_14_edge_case_boundary": {
        "description": "Variance exactly at 0.5% boundary (is it green or yellow?)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 100.5, "price_usd": 500, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected_output": {
            "status": "AUTO_APPROVE",                      # At boundary = safe
            "confidence": 100,
            "variance_severity": "GREEN",
            "fraud_score": 5,
            "reason": "At 0.5% boundary - within acceptable tolerance"
        }
    },
    
    "scenario_15_extreme_variance": {
        "description": "Extreme variance > 10% (almost certainly fraud or error)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 150, "price_usd": 400, "date": "2024-04-15"},
        "receipt": {"qty_mt": 80, "date": "2024-04-10"},
        "expected_output": {
            "status": "ESCALATE_TO_DIRECTOR",
            "confidence": 10,
            "variance_severity": "RED",
            "fraud_score": 95,
            "financial_exposure_usd": 8000,               # Large potential loss
            "recommendation": "REJECT - EXTREME DISCREPANCY"
        }
    }
}
```

### **Test Runner Function**

```python
def run_all_reconciliation_tests():
    """
    Run all 15 test scenarios and generate report.
    
    Returns:
    {
        "total_tests": 15,
        "passed": int,
        "failed": int,
        "test_results": [
            {
                "scenario": str,
                "description": str,
                "agent_output": dict,
                "expected_output": dict,
                "passed": bool,
                "discrepancies": list,
                "error": str (if failed)
            }
        ],
        "summary": {
            "pass_rate": float,
            "critical_issues": int,
            "coverage": dict
        }
    }
    """
```

---

## ENHANCED: app.py (Updated UI/UX)

### **Page 2: Reconciliation Agent - ENHANCED**

**New Section: Variance Visualization**

```python
st.subheader("📊 Variance Analysis")

# Create 3-column layout for variance metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Qty Variance",
        f"{variance_pct:.2f}%",
        delta=f"{qty_diff} MT",
        delta_color="inverse",
        help="Contract vs Invoice variance"
    )

with col2:
    st.metric(
        "Price Variance",
        f"{price_pct:.2f}%",
        delta=f"${price_diff:.2f}",
        delta_color="inverse"
    )

with col3:
    st.metric(
        "Timeline Gap",
        f"{days_diff} days",
        delta_color="normal",
        help="Days between receipt and invoice"
    )

# Variance Severity Gauge
st.write("**Variance Severity:**")
variance_level = agent_result['variance_analysis']['severity']
colors = {"GREEN": "🟢", "YELLOW": "🟡", "ORANGE": "🟠", "RED": "🔴"}
st.write(f"{colors[variance_level]} {variance_level}")

# Detailed Variance Table
st.write("**Detailed Breakdown:**")
variance_df = pd.DataFrame([
    {
        "Dimension": "Quantity (MT)",
        "Contract": contract['qty_mt'],
        "Invoice": invoice['qty_mt'],
        "Receipt": receipt['qty_mt'],
        "Variance %": f"{result['variance_analysis']['qty_variance']['variance_contract_to_invoice_pct']:.2f}%",
        "Status": "✅" if result['variance_analysis']['qty_variance']['qty_matches']['contract_vs_invoice'] else "⚠️"
    },
    {
        "Dimension": "Price (USD)",
        "Contract": f"${contract['price_usd']}",
        "Invoice": f"${invoice['price_usd']}",
        "Receipt": "N/A",
        "Variance %": f"{result['variance_analysis']['price_variance']['variance_pct']:.2f}%",
        "Status": "✅" if result['variance_analysis']['price_variance']['price_match'] else "⚠️"
    },
    {
        "Dimension": "Timeline",
        "Contract": contract['date'],
        "Invoice": invoice['date'],
        "Receipt": receipt['date'],
        "Variance %": f"{result['variance_analysis']['timeline_variance']['days_diff']} days",
        "Status": "✅" if result['variance_analysis']['timeline_variance']['severity'] == "GREEN" else "⚠️"
    }
])

st.dataframe(variance_df, use_container_width=True)
```

**New Section: Fraud Detection**

```python
st.subheader("🚨 Fraud Detection Analysis")

fraud_data = agent_result['fraud_analysis']

# Fraud Score Gauge (0-100)
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    # Create visual fraud score bar
    fraud_score = fraud_data['fraud_score']
    if fraud_score < 25:
        color = "🟢"
        level = "LOW RISK"
    elif fraud_score < 50:
        color = "🟡"
        level = "MEDIUM RISK"
    elif fraud_score < 75:
        color = "🟠"
        level = "HIGH RISK"
    else:
        color = "🔴"
        level = "CRITICAL RISK"
    
    st.progress(fraud_score / 100)
    st.write(f"{color} **Fraud Score: {fraud_score}/100 - {level}**")

with col2:
    st.metric("Signals Detected", len(fraud_data['signals_detected']))

with col3:
    st.metric("Financial Exposure", f"${fraud_data['total_financial_exposure']:,.0f}")

# Fraud Signals Details
if fraud_data['signals_detected']:
    st.write("**Fraud Signals Detected:**")
    for signal in fraud_data['signals_detected']:
        with st.expander(f"🚩 {signal['signal_type']} ({signal['severity']})"):
            st.write(f"**Message:** {signal['message']}")
            st.write(f"**Severity:** {signal['severity']}")
            st.write(f"**Financial Impact:** ${signal['financial_exposure_usd']:,.2f}")
            st.write(f"**Pattern:** {signal['pattern']}")
            st.write(f"**Recommendation:** {signal['recommendation']}")
else:
    st.success("✅ No fraud signals detected")
```

**New Section: Anomaly Detection**

```python
st.subheader("⚠️ Anomaly Detection")

anomaly_data = agent_result['anomaly_analysis']

if anomaly_data['anomalies_detected']:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Anomalies", anomaly_data['total_anomalies'])
    
    with col2:
        st.metric("Critical Count", anomaly_data['critical_anomalies'])
    
    with col3:
        severity_counts = {
            "HIGH": len([a for a in anomaly_data['anomalies_detected'] if a['severity'] == "HIGH"]),
            "MEDIUM": len([a for a in anomaly_data['anomalies_detected'] if a['severity'] == "MEDIUM"]),
            "LOW": len([a for a in anomaly_data['anomalies_detected'] if a['severity'] == "LOW"])
        }
        st.metric("Distribution", f"H:{severity_counts['HIGH']} M:{severity_counts['MEDIUM']} L:{severity_counts['LOW']}")
    
    st.write("**Detected Anomalies:**")
    for anomaly in anomaly_data['anomalies_detected']:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**{anomaly['anomaly_type']}** - {anomaly['pattern']}")
            st.write(f"*{anomaly['description']}*")
            st.write(f"Confidence: {anomaly['confidence']:.1%}")
        
        with col2:
            severity_color = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}
            st.write(f"{severity_color[anomaly['severity']]} {anomaly['severity']}")
else:
    st.success("✅ No anomalies detected")
```

**New Section: Confidence Breakdown**

```python
st.subheader("📈 Confidence Score Breakdown")

confidence_data = agent_result['confidence_breakdown']

# Show penalty breakdown
col1, col2 = st.columns(2)

with col1:
    st.write("**Penalties Applied:**")
    st.write(f"- Initial Confidence: **{confidence_data['initial_confidence']}**")
    st.write(f"- Qty Variance Penalty: **-{confidence_data['qty_variance_penalty']}**")
    st.write(f"- Price Variance Penalty: **-{confidence_data['price_variance_penalty']}**")
    st.write(f"- Timeline Penalty: **-{confidence_data['timeline_penalty']}**")
    st.write(f"- Fraud Penalty: **-{confidence_data['fraud_penalty']}**")
    st.write(f"- Anomaly Penalty: **-{confidence_data['anomaly_penalty']}**")

with col2:
    # Visual breakdown
    penalties = {
        "Initial": confidence_data['initial_confidence'],
        "Qty": confidence_data['qty_variance_penalty'],
        "Price": confidence_data['price_variance_penalty'],
        "Timeline": confidence_data['timeline_penalty'],
        "Fraud": confidence_data['fraud_penalty'],
        "Anomaly": confidence_data['anomaly_penalty']
    }
    
    st.write("**Final Confidence:**")
    st.write(f"# {confidence_data['final_confidence']}%")
    
    # Color code based on final confidence
    if confidence_data['final_confidence'] > 95:
        st.success("✅ AUTO-APPROVE")
    elif confidence_data['final_confidence'] > 80:
        st.info("📋 Route to Specialist")
    elif confidence_data['final_confidence'] > 50:
        st.warning("⚠️ Escalate to Manager")
    else:
        st.error("🚫 Escalate to Director / REJECT")
```

**ENHANCED HITL Section:**

```python
st.subheader("👤 Human-in-the-Loop Approval")

# Show agent recommendation prominently
st.info(f"**Agent Recommendation:** {agent_result['status']} (Confidence: {agent_result['confidence']}%)")

# Side-by-side comparison table
st.write("**Document Comparison:**")
comparison_table = pd.DataFrame({
    "Field": ["Quantity (MT)", "Price (USD)", "Date"],
    "Contract": [contract['qty_mt'], contract['price_usd'], contract['date']],
    "Invoice": [invoice['qty_mt'], invoice['price_usd'], invoice['date']],
    "Receipt": [receipt['qty_mt'], "N/A", receipt['date']],
    "Status": [
        "✅" if abs(contract['qty_mt'] - invoice['qty_mt']) <= contract['qty_mt'] * 0.005 else "⚠️",
        "✅" if abs(contract['price_usd'] - invoice['price_usd']) <= contract['price_usd'] * 0.005 else "⚠️",
        "✅" if (datetime.strptime(invoice['date'], '%Y-%m-%d') - datetime.strptime(receipt['date'], '%Y-%m-%d')).days <= 5 else "⚠️"
    ]
})

st.dataframe(comparison_table, use_container_width=True)

# Issues requiring attention
if agent_result.get('issues_for_review'):
    st.write("**Issues Requiring Your Attention:**")
    for issue in agent_result['issues_for_review']:
        with st.expander(f"{issue['severity']} - {issue['issue_title']}"):
            st.write(f"**Description:** {issue['issue_description']}")
            st.write(f"**Impact:** {issue['impact']}")
            st.write(f"**Suggested Action:** {issue['suggested_action']}")

# Human decision input
st.write("---")
st.write("**Your Decision:**")

col1, col2, col3 = st.columns(3)
with col1:
    approve = st.button("✅ APPROVE", key="approve_btn", use_container_width=True)
with col2:
    reject = st.button("❌ REJECT", key="reject_btn", use_container_width=True)
with col3:
    request_info = st.button("❓ REQUEST_INFO", key="info_btn", use_container_width=True)

# Get human decision
human_decision = None
if approve:
    human_decision = "APPROVE"
elif reject:
    human_decision = "REJECT"
elif request_info:
    human_decision = "REQUEST_MORE_INFO"

if human_decision:
    # Additional information
    col1, col2 = st.columns(2)
    
    with col1:
        human_notes = st.text_area(
            "Your Justification:",
            placeholder="Explain why you approve/reject/request info...",
            height=100
        )
    
    with col2:
        human_confidence = st.slider(
            "Your Confidence in This Decision:",
            min_value=0,
            max_value=100,
            value=85,
            step=5,
            help="How confident are you in your decision?"
        )
    
    # Submit button
    if st.button("✅ SUBMIT DECISION", use_container_width=True):
        # Log to audit trail
        approval_record = guardrails.log_human_approval(
            audit_id=agent_result['audit_id'],
            approver=st.session_state.get('user_email', 'demo_user@bunge.com'),
            decision=human_decision,
            notes=human_notes,
            confidence=human_confidence
        )
        
        # Show result
        st.success(f"✅ Decision Recorded: {human_decision}")
        st.write(f"**Audit ID:** {agent_result['audit_id']}")
        st.write(f"**Your Confidence:** {human_confidence}%")
        st.write(f"**Approver:** {approval_record['approver']}")
        st.write(f"**Notes:** {human_notes}")
```

---

## NEW: run_tests.py

```python
"""
Master test runner for all scenarios.
Generates comprehensive test report.
"""

def main():
    """
    Run all tests and generate report.
    
    Tests:
    1. reconciliation_agent tests (15 scenarios)
    2. doc_agent tests (5 scenarios)
    3. guardrails tests
    4. database tests
    5. variance calculation tests
    6. fraud detection tests
    7. anomaly detection tests
    
    Output:
    - Console report (pass/fail for each)
    - HTML report (detailed with screenshots)
    - CSV export (for analysis)
    """
```

**Usage:**
```bash
python run_tests.py
```

---

## ADDITIONAL FEATURES (BACKEND)

### **Financial Impact Calculation**

Add to `reconciliation_agent.py`:

```python
def calculate_financial_impact(self, contract: dict, invoice: dict, receipt: dict, anomalies: list) -> dict:
    """
    Calculate potential financial loss/exposure.
    
    Scenarios:
    1. Qty overstatement: (invoice_qty - receipt_qty) * invoice_price = $ at risk
    2. Price manipulation: abs(invoice_price - contract_price) * contract_qty = $ at risk
    3. Duplicate invoice: full invoice amount = $ at risk (if duplicate found)
    
    Returns:
    {
        "qty_overstatement_exposure": float,
        "price_anomaly_exposure": float,
        "duplicate_risk_exposure": float,
        "total_exposure": float,
        "exposure_level": "LOW|MEDIUM|HIGH|CRITICAL"
    }
    """
```

### **Decision Recommendation Engine**

Add to `guardrails.py`:

```python
def generate_recommendation(self, agent_result: dict) -> str:
    """
    Generate recommended action based on all analysis.
    
    Logic:
    - Fraud Score > 80: "ESCALATE_FOR_INVESTIGATION"
    - Confidence > 95: "AUTO_APPROVE"
    - Confidence 80-95: "ROUTE_TO_SPECIALIST"
    - Confidence 50-80: "ESCALATE_TO_MANAGER"
    - Confidence < 50: "ESCALATE_TO_DIRECTOR"
    - Multiple critical anomalies: "REJECT"
    
    Returns: str (recommendation text)
    """
```

### **Historical Pattern Tracking** (Optional Enhancement)

Add to `database.py`:

```python
def get_similar_past_decisions(self, current_decision: dict, limit: int = 5) -> list:
    """
    Find similar past decisions for comparison.
    
    Useful for:
    - "This similar shipment was approved in the past"
    - "This pattern usually gets escalated"
    - Building confidence in decisions
    
    Returns: List of similar past decisions
    """
```

---

## TESTING CHECKLIST

### **Unit Tests (reconciliation_agent.py)**

```python
def test_variance_calculations():
    """Test variance calculation formulas"""
    assert calculate_qty_variance(100, 102, 100) == {variance: 2%, status: "YELLOW"}
    assert calculate_price_variance(500, 495) == {variance: -1%, status: "YELLOW"}
    # ... more assertions

def test_fraud_detection():
    """Test fraud signals"""
    result = detect_fraud_signals(
        contract={qty: 100, price: 500},
        invoice={qty: 110, price: 450},
        receipt={qty: 100}
    )
    assert "SUSPICIOUS_PRICE_QTY_COMBO" in result['signals']
    assert result['fraud_score'] > 80

def test_anomaly_detection():
    """Test anomaly detection"""
    result = detect_all_anomalies(...)
    assert len(result['anomalies']) >= 2

def test_confidence_calculation():
    """Test confidence score formula"""
    # Perfect match = 100
    assert calculate_confidence(no_variance, no_anomalies) == 100
    # With penalties
    assert calculate_confidence(variance=2%, anomalies=2) < 95
```

### **Integration Tests (run_tests.py)**

```python
def test_scenario_01_perfect_match():
    """Test perfect match scenario"""
    result = agent.reconcile(
        contract={"qty_mt": 100, ...},
        invoice={"qty_mt": 100, ...},
        receipt={"qty_mt": 100, ...}
    )
    assert result['status'] == "AUTO_APPROVE"
    assert result['confidence'] == 100

def test_scenario_09_fraud_signal():
    """Test fraud signal scenario"""
    result = agent.reconcile(
        contract={"qty_mt": 100, "price_usd": 500},
        invoice={"qty_mt": 115, "price_usd": 450},
        receipt={"qty_mt": 100}
    )
    assert result['status'] == "ESCALATE_TO_DIRECTOR"
    assert result['fraud_analysis']['fraud_score'] > 80
    assert "SUSPICIOUS_PRICE_QTY_COMBO" in [s['signal_type'] for s in result['fraud_analysis']['signals_detected']]

def test_scenario_15_extreme_variance():
    """Test extreme variance scenario"""
    result = agent.reconcile(
        contract={"qty_mt": 100, ...},
        invoice={"qty_mt": 150, ...},
        receipt={"qty_mt": 80, ...}
    )
    assert result['status'] == "ESCALATE_TO_DIRECTOR"
    assert result['confidence'] < 20
```

### **UI Tests**

```python
def test_hitl_workflow():
    """Test HITL approval workflow"""
    # Simulate user approval
    approval = guardrails.process_human_decision(
        audit_id="AUD-12345",
        human_decision="APPROVE",
        human_notes="Verified with sales",
        human_confidence=92
    )
    assert approval['final_status'] == "APPROVED"
    assert approval['human_decision'] == "APPROVE"

def test_variance_display():
    """Test variance visualization data structure"""
    display_data = create_hitl_display_data(agent_recommendation)
    assert 'variance_summary' in display_data
    assert 'comparison_table' in display_data
    assert 'fraud_summary' in display_data
```

---

## IMPLEMENTATION PRIORITIES (UPDATED)

**Day 1 (Core + Tests):**
1. ✅ database.py
2. ✅ guardrails.py
3. ✅ reconciliation_agent.py (with VarianceCalculator + FraudDetector + AnomalyDetector)
4. ✅ test_reconciliation_scenarios.py (15 scenarios)
5. ✅ run_tests.py (test runner)

**Day 2 (UI + Doc Agent):**
6. ✅ app.py (Reconciliation page - ENHANCED with variance/fraud/anomaly sections + HITL)
7. ✅ doc_agent.py
8. ✅ app.py (LC Doc page)

**Day 3 (Polish + Complete):**
9. ✅ app.py (Audit Trail + Dashboard pages)
10. ✅ Mock data files (15 + 5 scenarios as JSON)
11. ✅ README.md
12. ✅ All tests passing
13. ✅ Test report generated

---

## SUCCESS CRITERIA (UPDATED)

✅ **Reconciliation Agent:**
- Correctly calculates variance (qty, price, timeline) with percentages
- Detects 9+ fraud signals (qty overstatement, price manipulation, timeline issues, duplicates)
- Detects 8+ anomaly patterns
- Routes based on confidence + fraud + anomalies
- All 15 test scenarios pass

✅ **Variance Analysis:**
- Shows 3-dimensional variance (contract↔invoice, invoice↔receipt, contract↔receipt)
- Calculates variance % with proper formulas
- Classifies severity (GREEN <0.5%, YELLOW 0.5-2%, ORANGE 2-5%, RED >5%)
- Visual display in UI

✅ **Fraud Detection:**
- Detects PRICE_DOWN + QTY_UP suspicious combo
- Detects invoice before receipt (impossible timeline)
- Calculates fraud_score (0-100)
- Shows financial exposure for each fraud signal

✅ **Anomaly Detection:**
- Detects qty mismatches (contract↔invoice, invoice↔receipt, circular)
- Detects logical inconsistencies
- Shows confidence level for each anomaly
- Counts critical vs high vs low anomalies

✅ **HITL Workflow:**
- Shows agent recommendation clearly
- Side-by-side comparison table
- All variance/fraud/anomaly details visible
- Approval buttons: [APPROVE] [REJECT] [REQUEST_INFO]
- Human notes + confidence capture
- Decision logged to audit trail

✅ **UI/UX:**
- Variance visualization with metrics + table
- Fraud detection with score gauge + signal details
- Anomaly detection with severity breakdown
- HITL with clear decision options
- Color coding (🟢 🟡 🟠 🔴)
- Progress bars + meters

✅ **Testing:**
- 15 reconciliation test scenarios (all pass)
- 5 LC doc test scenarios (all pass)
- Test runner generates report
- Coverage for variance, fraud, anomaly detection

---

## FINAL CHECKLIST

```
BACKEND:
☐ reconciliation_agent.py with VarianceCalculator class
☐ reconciliation_agent.py with FraudDetector class
☐ reconciliation_agent.py with AnomalyDetector class
☐ guardrails.py with HITLWorkflow class
☐ database.py (ChromaDB + SQLite)
☐ doc_agent.py (LC validation)
☐ run_tests.py (test runner)

FRONTEND:
☐ app.py - Reconciliation page (complete)
☐ Variance Analysis section (metrics + table)
☐ Fraud Detection section (score + signals)
☐ Anomaly Detection section (table + severity)
☐ HITL Workflow section (comparison + approval)
☐ Confidence Breakdown section
☐ app.py - LC Doc page
☐ app.py - Audit Trail page
☐ app.py - Dashboard page

TESTS:
☐ 15 reconciliation scenarios (JSON files)
☐ 5 LC doc scenarios (JSON files)
☐ test_reconciliation_scenarios.py
☐ test_fraud_detection.py
☐ test_anomaly_detection.py
☐ test_variance_calculations.py
☐ Test results: ALL PASS

DATA:
☐ Mock contract.csv
☐ Mock invoice.csv
☐ Mock receipt.csv
☐ Sample LC.txt
☐ 15 + 5 test scenario JSON files

DOCUMENTATION:
☐ README.md (complete)
☐ .env.example
☐ requirements.txt
☐ Code comments (well-documented)
☐ Test report generated

Ready for demo & interview!
```

---

## END OF UPDATED SPEC SHEET

This comprehensive spec includes:
- ✅ 3-way variance calculations (3 dimensions)
- ✅ Fraud detection (9+ signals, fraud_score 0-100)
- ✅ Anomaly detection (8+ patterns)
- ✅ Financial impact calculation
- ✅ Enhanced HITL workflow with detailed UI
- ✅ 15 comprehensive test scenarios
- ✅ Test runner + report generation
- ✅ Enhanced Streamlit UI with variance/fraud/anomaly visualization
- ✅ All edge cases covered

Ready for Claude Code implementation! 🚀
