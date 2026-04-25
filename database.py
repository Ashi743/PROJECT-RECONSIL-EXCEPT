import sqlite3
import chromadb
import json
from datetime import datetime
from typing import Dict, List, Optional


class Database:
    """Manages ChromaDB (vector storage) and SQLite (audit trail)."""

    def __init__(self):
        """Initialize database connections."""
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection("lc_documents")
        self.db_path = "audit_logs.db"
        self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite database with audit tables and exception tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                audit_id TEXT UNIQUE NOT NULL,
                agent TEXT NOT NULL,
                decision TEXT NOT NULL,
                confidence INTEGER NOT NULL,
                reasoning TEXT,
                status TEXT DEFAULT 'awaiting_approval',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS human_approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                approver TEXT NOT NULL,
                human_decision TEXT NOT NULL,
                human_notes TEXT,
                human_confidence INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (audit_id) REFERENCES audit_trail(audit_id)
            )
        """)

        # Exception tables for Exception Triage Agent
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exceptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exception_id TEXT UNIQUE NOT NULL,
                exception_type TEXT NOT NULL,
                original_message TEXT NOT NULL,
                classification_confidence INTEGER,
                urgency TEXT NOT NULL,
                urgency_score INTEGER,
                handler TEXT NOT NULL,
                owner TEXT NOT NULL,
                deadline TEXT NOT NULL,
                deadline_timestamp TEXT NOT NULL,
                action_plan TEXT NOT NULL,
                financial_impact REAL,
                context TEXT,
                status TEXT DEFAULT 'OPEN',
                created_at TEXT NOT NULL,
                updated_at TEXT,
                resolved_at TEXT,
                audit_id TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shipments (
                shipment_id TEXT PRIMARY KEY,
                vessel_name TEXT NOT NULL,
                expected_arrival TEXT NOT NULL,
                actual_arrival TEXT,
                status TEXT DEFAULT 'IN_TRANSIT',
                daily_dd_rate REAL DEFAULT 50000
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lcs (
                lc_id TEXT PRIMARY KEY,
                lc_number TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                lc_amount REAL NOT NULL,
                required_documents TEXT NOT NULL,
                received_documents TEXT,
                status TEXT DEFAULT 'ACTIVE'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vessels (
                vessel_name TEXT PRIMARY KEY,
                port TEXT NOT NULL,
                laytime_expiry TEXT NOT NULL,
                daily_dd_rate REAL DEFAULT 50000,
                status TEXT DEFAULT 'DISCHARGING'
            )
        """)

        conn.commit()
        conn.close()

    def add_lc_to_vectordb(self, lc_text: str, lc_id: str, metadata: dict) -> None:
        """
        Add LC document to ChromaDB with embeddings.

        Args:
            lc_text: Full LC document text
            lc_id: Unique LC identifier
            metadata: Document metadata (date, counterparty, etc.)
        """
        try:
            self.collection.add(
                documents=[lc_text],
                metadatas=[metadata],
                ids=[lc_id]
            )
        except Exception as e:
            print(f"Error adding LC to ChromaDB: {e}")
            raise

    def search_similar_lcs(self, query: str, top_k: int = 3) -> Dict:
        """
        Search for similar LC documents in ChromaDB.

        Args:
            query: Search query text
            top_k: Number of results to return

        Returns:
            Dict with results and metadata
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            return {
                "documents": results.get("documents", []),
                "metadatas": results.get("metadatas", []),
                "ids": results.get("ids", []),
                "distances": results.get("distances", [])
            }
        except Exception as e:
            print(f"Error searching ChromaDB: {e}")
            return {"documents": [], "metadatas": [], "ids": [], "distances": []}

    def get_lc_by_id(self, lc_id: str) -> Optional[Dict]:
        """
        Retrieve specific LC document by ID.

        Args:
            lc_id: Unique LC identifier

        Returns:
            Dict with document data or None if not found
        """
        try:
            results = self.collection.get(ids=[lc_id])
            if results and results.get("documents"):
                return {
                    "id": lc_id,
                    "document": results["documents"][0],
                    "metadata": results["metadatas"][0] if results.get("metadatas") else {}
                }
            return None
        except Exception as e:
            print(f"Error retrieving LC from ChromaDB: {e}")
            return None

    def log_agent_decision(self, agent: str, decision: dict, confidence: int, reasoning: str) -> str:
        """
        Log agent decision to audit trail (append-only).

        Args:
            agent: Agent name (reconciliation_agent | doc_agent)
            decision: Decision dict (must be JSON serializable)
            confidence: Confidence score (0-100)
            reasoning: Reasoning text

        Returns:
            audit_id for reference
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            import secrets
            audit_id = f"AUD-{secrets.token_hex(4).upper()}"
            timestamp = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO audit_trail (timestamp, audit_id, agent, decision, confidence, reasoning, status)
                VALUES (?, ?, ?, ?, ?, ?, 'awaiting_approval')
            """, (
                timestamp,
                audit_id,
                agent,
                json.dumps(decision),
                confidence,
                reasoning
            ))

            conn.commit()
            return audit_id
        except Exception as e:
            print(f"Error logging decision: {e}")
            raise
        finally:
            conn.close()

    def log_human_approval(self, audit_id: str, approver: str, decision: str, notes: str, confidence: int) -> None:
        """
        Log human approval decision (append-only).

        Args:
            audit_id: Reference to agent decision
            approver: Approver name/email
            decision: Human decision (APPROVE | REJECT | REQUEST_INFO)
            notes: Human notes
            confidence: Human confidence (0-100)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            timestamp = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO human_approvals (audit_id, timestamp, approver, human_decision, human_notes, human_confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                audit_id,
                timestamp,
                approver,
                decision,
                notes,
                confidence
            ))

            # Update audit_trail status
            cursor.execute("""
                UPDATE audit_trail
                SET status = 'approved'
                WHERE audit_id = ?
            """, (audit_id,))

            conn.commit()
        except Exception as e:
            print(f"Error logging human approval: {e}")
            raise
        finally:
            conn.close()

    def get_audit_trail(self, limit: int = 50) -> List[Dict]:
        """
        Get recent audit trail entries with human approvals joined.

        Args:
            limit: Number of recent entries to return

        Returns:
            List of audit trail entries with approval info
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    at.audit_id,
                    at.timestamp,
                    at.agent,
                    at.decision,
                    at.confidence,
                    at.reasoning,
                    at.status,
                    ha.approver,
                    ha.human_decision,
                    ha.human_notes,
                    ha.human_confidence
                FROM audit_trail at
                LEFT JOIN human_approvals ha ON at.audit_id = ha.audit_id
                ORDER BY at.created_at DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append({
                    "audit_id": row[0],
                    "timestamp": row[1],
                    "agent": row[2],
                    "decision": json.loads(row[3]) if row[3] else {},
                    "confidence": row[4],
                    "reasoning": row[5],
                    "status": row[6],
                    "approver": row[7],
                    "human_decision": row[8],
                    "human_notes": row[9],
                    "human_confidence": row[10]
                })
            return result
        except Exception as e:
            print(f"Error retrieving audit trail: {e}")
            return []
        finally:
            conn.close()

    def get_decision_by_audit_id(self, audit_id: str) -> Optional[Dict]:
        """
        Get specific decision by audit ID.

        Args:
            audit_id: Unique audit identifier

        Returns:
            Dict with decision and approval details or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    at.audit_id,
                    at.timestamp,
                    at.agent,
                    at.decision,
                    at.confidence,
                    at.reasoning,
                    at.status,
                    ha.approver,
                    ha.human_decision,
                    ha.human_notes,
                    ha.human_confidence
                FROM audit_trail at
                LEFT JOIN human_approvals ha ON at.audit_id = ha.audit_id
                WHERE at.audit_id = ?
            """, (audit_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "audit_id": row[0],
                    "timestamp": row[1],
                    "agent": row[2],
                    "decision": json.loads(row[3]) if row[3] else {},
                    "confidence": row[4],
                    "reasoning": row[5],
                    "status": row[6],
                    "approver": row[7],
                    "human_decision": row[8],
                    "human_notes": row[9],
                    "human_confidence": row[10]
                }
            return None
        except Exception as e:
            print(f"Error retrieving decision: {e}")
            return None
        finally:
            conn.close()

    # ============================================================================
    # EXCEPTION MANAGEMENT METHODS (For Exception Triage Agent)
    # ============================================================================

    def save_exception(self, exception_data: dict) -> str:
        """Save exception to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO exceptions
                (exception_id, exception_type, original_message, classification_confidence,
                 urgency, urgency_score, handler, owner, deadline, deadline_timestamp,
                 action_plan, financial_impact, context, status, created_at, audit_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                exception_data["exception_id"],
                exception_data["exception_type"],
                exception_data["original_message"],
                exception_data["classification_confidence"],
                exception_data["urgency"],
                exception_data["urgency_score"],
                exception_data["handler"],
                exception_data["owner"],
                exception_data["deadline"],
                exception_data["deadline_timestamp"],
                json.dumps(exception_data["action_plan"]),
                exception_data["financial_impact"],
                json.dumps(exception_data["context"]) if isinstance(exception_data.get("context"), dict) else exception_data.get("context"),
                exception_data["status"],
                exception_data["created_at"],
                exception_data.get("audit_id")
            ))

            conn.commit()
            return exception_data["exception_id"]
        except Exception as e:
            print(f"Error saving exception: {e}")
            return ""
        finally:
            conn.close()

    def get_exception(self, exception_id: str) -> Optional[Dict]:
        """Retrieve exception by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM exceptions WHERE exception_id = ?
            """, (exception_id,))

            row = cursor.fetchone()
            if row:
                cols = [col[0] for col in cursor.description]
                exception = dict(zip(cols, row))
                if exception.get("action_plan"):
                    try:
                        exception["action_plan"] = json.loads(exception["action_plan"])
                    except:
                        exception["action_plan"] = []
                if exception.get("context"):
                    try:
                        exception["context"] = json.loads(exception["context"])
                    except:
                        exception["context"] = {}
                return exception
            return None
        except Exception as e:
            print(f"Error retrieving exception: {e}")
            return None
        finally:
            conn.close()

    def update_exception_status(self, exception_id: str, status: str) -> None:
        """Update exception status (OPEN → IN_PROGRESS → RESOLVED)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            resolved_at = datetime.now().isoformat() if status == 'RESOLVED' else None
            cursor.execute("""
                UPDATE exceptions
                SET status = ?, updated_at = ?, resolved_at = ?
                WHERE exception_id = ?
            """, (status, datetime.now().isoformat(), resolved_at, exception_id))

            conn.commit()
        except Exception as e:
            print(f"Error updating exception status: {e}")
        finally:
            conn.close()

    def get_active_exceptions(self, urgency: str = None) -> List[Dict]:
        """Get all OPEN or IN_PROGRESS exceptions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if urgency:
                cursor.execute("""
                    SELECT * FROM exceptions
                    WHERE status IN ('OPEN', 'IN_PROGRESS') AND urgency = ?
                    ORDER BY urgency_score DESC
                """, (urgency,))
            else:
                cursor.execute("""
                    SELECT * FROM exceptions
                    WHERE status IN ('OPEN', 'IN_PROGRESS')
                    ORDER BY urgency_score DESC
                """)

            rows = cursor.fetchall()
            cols = [col[0] for col in cursor.description]

            exceptions = []
            for row in rows:
                exc = dict(zip(cols, row))
                if exc.get("action_plan"):
                    try:
                        exc["action_plan"] = json.loads(exc["action_plan"])
                    except:
                        exc["action_plan"] = []
                if exc.get("context"):
                    try:
                        exc["context"] = json.loads(exc["context"])
                    except:
                        exc["context"] = {}
                exceptions.append(exc)

            return exceptions
        except Exception as e:
            print(f"Error retrieving active exceptions: {e}")
            return []
        finally:
            conn.close()

    def get_exceptions_by_urgency(self, urgency: str) -> List[Dict]:
        """Get exceptions of specific urgency level."""
        return self.get_active_exceptions(urgency=urgency)

    def exception_exists(self, identifier: str, exception_type: str) -> bool:
        """Check if exception already exists for this shipment/LC/vessel."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT COUNT(*) FROM exceptions
                WHERE status IN ('OPEN', 'IN_PROGRESS')
                AND exception_type = ?
                AND (context LIKE ? OR original_message LIKE ?)
            """, (exception_type, f'%{identifier}%', f'%{identifier}%'))

            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            print(f"Error checking exception existence: {e}")
            return False
        finally:
            conn.close()

    def get_shipments_in_transit(self) -> List[Dict]:
        """Get all shipments with status='IN_TRANSIT'."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM shipments WHERE status = 'IN_TRANSIT'
            """)

            rows = cursor.fetchall()
            cols = [col[0] for col in cursor.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            print(f"Error retrieving shipments: {e}")
            return []
        finally:
            conn.close()

    def get_active_lcs(self) -> List[Dict]:
        """Get all LCs with status='ACTIVE'."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM lcs WHERE status = 'ACTIVE'
            """)

            rows = cursor.fetchall()
            cols = [col[0] for col in cursor.description]
            lcs = []
            for row in rows:
                lc = dict(zip(cols, row))
                if lc.get("required_documents"):
                    try:
                        lc["required_documents"] = json.loads(lc["required_documents"])
                    except:
                        lc["required_documents"] = []
                if lc.get("received_documents"):
                    try:
                        lc["received_documents"] = json.loads(lc["received_documents"])
                    except:
                        lc["received_documents"] = []
                lcs.append(lc)
            return lcs
        except Exception as e:
            print(f"Error retrieving LCs: {e}")
            return []
        finally:
            conn.close()

    def get_vessels_discharging(self) -> List[Dict]:
        """Get all vessels with status='DISCHARGING'."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM vessels WHERE status = 'DISCHARGING'
            """)

            rows = cursor.fetchall()
            cols = [col[0] for col in cursor.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            print(f"Error retrieving vessels: {e}")
            return []
        finally:
            conn.close()

    def get_recent_reconciliations(self, limit: int = 50) -> List[Dict]:
        """Get recent reconciliation decisions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM audit_trail
                WHERE agent = 'ReconciliationAgent'
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            cols = [col[0] for col in cursor.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            print(f"Error retrieving reconciliations: {e}")
            return []
        finally:
            conn.close()

    def get_auto_approve_rate(self) -> float:
        """Calculate % of reconciliations with status=AUTO_APPROVE."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN decision LIKE '%AUTO_APPROVE%' THEN 1 ELSE 0 END) as approved
                FROM audit_trail
                WHERE agent = 'ReconciliationAgent'
            """)

            row = cursor.fetchone()
            total = row[0] if row[0] else 1
            approved = row[1] if row[1] else 0

            return (approved / total) if total > 0 else 0.0
        except Exception as e:
            print(f"Error calculating auto-approve rate: {e}")
            return 0.0
        finally:
            conn.close()

    def get_total_financial_exposure(self) -> float:
        """Sum of all financial_impact values from active exceptions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT SUM(financial_impact) FROM exceptions
                WHERE status IN ('OPEN', 'IN_PROGRESS')
            """)

            row = cursor.fetchone()
            return row[0] if row[0] else 0.0
        except Exception as e:
            print(f"Error calculating financial exposure: {e}")
            return 0.0
        finally:
            conn.close()
