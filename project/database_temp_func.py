
def find_recommendation(text: str) -> str:
    if not text:
        return None
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT item_name, plan_release, weight FROM recommendations WHERE is_active=1")
        rows = cur.fetchall()
        
        matches = []
        for item_name, plan_release, weight in rows:
            if item_name and item_name in text:
                matches.append((item_name, plan_release, weight))
        
        # Sort by weight (desc), then by length of item_name (desc) (longer match is more specific)
        if matches:
            matches.sort(key=lambda x: (x[2], len(x[0])), reverse=True)
            return matches[0][1]
        return None
    finally:
        conn.close()
