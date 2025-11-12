# memory.py
import csv
import os
import json
from typing import Dict, Any


import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from state_module.state import State  # Import State class for managing state names

import uuid
from mem0 import Memory as Mem0Memory

class Memory:
    def __init__(self, user_id: str, session_id: str, mem0_config: Dict[str, Any]):
        self.user_id = user_id
        self.mem0 = Mem0Memory.from_config(mem0_config)
        if session_id not None self.session_id = session_id else session_id =  str(uuid.uuid4())


    def start_new_session(self):
        """Start a new chat session."""
        self.session_id = str(uuid.uuid4())
        return self.session_id

    def add_memory(self, message: str, role: str = "user") -> bool:
        """Add a single turn to memory (user or assistant)."""
        try:
            metadata = {
                "user_id": self.user_id,
                "session_id": self.session_id,
                "role": role
            }
            self.mem0.add(message, metadata=metadata, user_id=self.user_id)



            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO conversation_context (user_id, role, message)
                VALUES (%s, %s, %s)
                """,
                (self.user_id, role, message)
            )
            conn.commit()
            cur.close()
            conn.close()

            return True



        except Exception as e:
            print(f"[Memory Error] Adding memory: {e}")
            return False

    def retrieve_memory(self, query: str = "", mem0_limit: int = 50, context_limit: int = 5) -> Dict[str, Any]:
        """
        Retrieve relevant memories for the current session.

        Args:
            query: Query string to search relevant memories.
            mem0_limit: Number of memories Mem0 returns.
            context_limit: Number of conversation turns to return for building context.

        Returns:
            {
                "conversation_ctx": str,        # combined string for LLM
                "retrieved_memories": list[str] # individual memory strings
            } or {"error": "retrieval failed"}
        """
        try:
            # Retrieve from Mem0
            results = self.mem0.search(
                query=query,
                user_id=self.user_id,
                limit=mem0_limit,
                metadata_filter={"session_id": self.session_id}
            )

            # Extract messages and truncate to context_limit
            messages = [f"{r['metadata']['role']}: {r['memory']}" for r in results["results"]]

            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute(
                """
                SELECT role, message FROM conversation_context
                WHERE user_id = %s
                ORDER BY id ASC
                """,
                (self.user_id,)
            )
            ctx_rows = cur.fetchall()
            conversation_ctx = "\n".join(f"{role}: {msg}" for role, msg in ctx_rows)
            cur.close()
            conn.close()

            return {
                "conversation_ctx":  conversation_ctx,
                "retrieved_memories": messages
            }

        except Exception as e:
            print(f"[Memory Error] Retrieving memory: {e}")
            return {"error": "retrieval failed"}
:
    pass
