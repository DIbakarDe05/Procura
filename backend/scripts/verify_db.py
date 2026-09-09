"""
Procura — Database & Vector DB Verification Script

Checks:
1. SQLite connection and table schema
2. Total standards and references
3. Vector embeddings stored in SQLite
4. Cosine similarity retrieval execution
"""

import sys
import os
import sqlite3
import json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "procura.db")

def main():
    print("=" * 65)
    print("  PROCURA — Database & Vector Store Verification")
    print("=" * 65)
    print(f"Database Path: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print(f"[FAIL] Database file not found at {DB_PATH}!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Check Tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"\n[1] Tables in DB ({len(tables)} found):")
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cursor.fetchone()[0]
        print(f"    - {t:<22} : {cnt:>5} records")

    # 2. Check BIS Standards & Embeddings
    cursor.execute("SELECT COUNT(*) FROM bis_standards;")
    total_standards = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bis_standards WHERE embedding IS NOT NULL AND embedding != '';")
    embedded_standards = cursor.fetchone()[0]

    print(f"\n[2] BIS Standards & Vector Embeddings:")
    print(f"    - Total Standards      : {total_standards}")
    print(f"    - Embedded Standards   : {embedded_standards}")

    if embedded_standards > 0:
        cursor.execute("SELECT standard_number, title, embedding FROM bis_standards WHERE embedding IS NOT NULL LIMIT 1;")
        std_num, title, emb_raw = cursor.fetchone()
        vec = json.loads(emb_raw)
        print(f"    - Sample Standard      : {std_num} — {title[:40]}...")
        print(f"    - Embedding Dimension  : {len(vec)} dimensions (stored as JSON vector)")
        print(f"    - Vector Type          : float list, parsed to numpy.float32")
        print(f"    - Vector norm          : {np.linalg.norm(np.array(vec, dtype=np.float32)):.4f}")
    else:
        print("    - [NOTE] No vector embeddings found in bis_standards yet.")

    # 3. Test Vector Cosine Similarity Search
    print(f"\n[3] Vector Search Engine Simulation:")
    if embedded_standards > 0:
        cursor.execute("SELECT id, standard_number, title, scope, embedding FROM bis_standards WHERE embedding IS NOT NULL;")
        all_std = cursor.fetchall()

        # Use the first standard's embedding as a query test vector
        query_vec = np.array(json.loads(all_std[0][4]), dtype=np.float32)

        results = []
        for sid, snum, stitle, sscope, semb in all_std:
            v = np.array(json.loads(semb), dtype=np.float32)
            sim = float(np.dot(query_vec, v) / (np.linalg.norm(query_vec) * np.linalg.norm(v)))
            results.append((snum, stitle, sim))

        results.sort(key=lambda x: x[2], reverse=True)
        print(f"    Vector retrieval executed against {len(all_std)} standards.")
        print("    Top 3 Cosine Similarity matches for sample query vector:")
        for rank, (snum, stitle, sim) in enumerate(results[:3], 1):
            print(f"      {rank}. {snum:<20} | Sim: {sim*100:5.1f}% | {stitle[:40]}")
    else:
        print("    - Cannot simulate vector search without stored embeddings.")

    # 4. Check Standard References Graph
    cursor.execute("SELECT COUNT(*) FROM standard_references;")
    total_refs = cursor.fetchone()[0]
    print(f"\n[4] Standard References (Relational Graph):")
    print(f"    - Total Links: {total_refs}")
    cursor.execute("""
        SELECT sr.reference_type, s1.standard_number, s2.standard_number 
        FROM standard_references sr
        JOIN bis_standards s1 ON sr.standard_id = s1.id
        JOIN bis_standards s2 ON sr.referenced_standard_id = s2.id
        LIMIT 3;
    """)
    for rtype, fnum, tnum in cursor.fetchall():
        print(f"      • {fnum} --[{rtype}]--> {tnum}")

    conn.close()

    print("\n" + "=" * 65)
    print("  VERIFICATION RESULT: ALL DB & VECTOR ENGINE CHECKS COMPLETE")
    print("=" * 65)

if __name__ == "__main__":
    main()
