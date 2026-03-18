
def get_ai_config(config_key='default'):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT provider, base_url, api_key, model_name, system_prompt FROM ai_config WHERE config_key=?", (config_key,))
        row = cur.fetchone()
        if row:
            return {
                "provider": row[0],
                "base_url": row[1],
                "api_key": row[2],
                "model_name": row[3],
                "system_prompt": row[4]
            }
        return None
    finally:
        conn.close()

def save_ai_config(config_key, provider, base_url, api_key, model_name, system_prompt):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO ai_config (config_key, provider, base_url, api_key, model_name, system_prompt)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(config_key) DO UPDATE SET
                provider=excluded.provider,
                base_url=excluded.base_url,
                api_key=excluded.api_key,
                model_name=excluded.model_name,
                system_prompt=excluded.system_prompt
            """,
            (config_key, provider, base_url, api_key, model_name, system_prompt)
        )
        conn.commit()
    finally:
        conn.close()
