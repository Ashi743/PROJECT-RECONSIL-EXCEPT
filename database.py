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
        """Initialize SQLite database with audit tables."""
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
