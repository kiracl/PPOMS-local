import os
import shutil
import pypdf
from docx import Document
import sqlite3
import database
from datetime import datetime

DOC_DIR = "knowledge_base_files"

def init_kb_dir():
    if not os.path.exists(DOC_DIR):
        os.makedirs(DOC_DIR)

def add_document(file_path):
    init_kb_dir()
    filename = os.path.basename(file_path)
    dest_path = os.path.join(DOC_DIR, filename)
    
    # Copy file to managed directory
    if os.path.abspath(file_path) != os.path.abspath(dest_path):
        shutil.copy2(file_path, dest_path)
        
    # Extract Text
    ext = os.path.splitext(filename)[1].lower()
    content = ""
    try:
        if ext == '.pdf':
            with open(dest_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    content += page.extract_text() + "\n"
        elif ext == '.docx':
            doc = Document(dest_path)
            for para in doc.paragraphs:
                content += para.text + "\n"
        elif ext in ['.txt', '.md']:
            with open(dest_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        else:
            return False, "不支持的文件格式"
            
        if not content.strip():
            return False, "文件内容为空或无法提取"

        # Save to DB
        conn = database._connect()
        cur = conn.cursor()
        
        # Check duplicate
        cur.execute("SELECT id FROM knowledge_docs WHERE filename=?", (filename,))
        if cur.fetchone():
            return False, "文件已存在"

        cur.execute(
            "INSERT INTO knowledge_docs (filename, filepath, doc_type, upload_time) VALUES (?, ?, ?, ?)",
            (filename, dest_path, ext, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        doc_id = cur.lastrowid
        
        # Chunking (Simple implementation: split by chunks of 500 chars)
        chunk_size = 500
        overlap = 50
        chunks = []
        for i in range(0, len(content), chunk_size - overlap):
            chunks.append(content[i:i+chunk_size])
            
        for i, chunk in enumerate(chunks):
            cur.execute(
                "INSERT INTO knowledge_chunks (doc_id, chunk_index, content) VALUES (?, ?, ?)",
                (doc_id, i, chunk)
            )
            # Add to FTS
            # FTS5 needs content and doc_id (UNINDEXED)
            cur.execute(
                "INSERT INTO knowledge_fts (content, doc_id) VALUES (?, ?)",
                (chunk, doc_id)
            )

        cur.execute("UPDATE knowledge_docs SET chunk_count=? WHERE id=?", (len(chunks), doc_id))
        conn.commit()
        conn.close()
        return True, "上传成功"

    except Exception as e:
        return False, str(e)

def delete_document(doc_id):
    conn = database._connect()
    cur = conn.cursor()
    cur.execute("SELECT filepath FROM knowledge_docs WHERE id=?", (doc_id,))
    row = cur.fetchone()
    if row:
        filepath = row[0]
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
    
    cur.execute("DELETE FROM knowledge_docs WHERE id=?", (doc_id,))
    # Cascade delete should handle chunks, but FTS needs manual delete?
    # FTS doesn't support foreign keys. We need to delete from FTS where doc_id matches.
    cur.execute("DELETE FROM knowledge_fts WHERE doc_id=?", (doc_id,))
    conn.commit()
    conn.close()
    return True

def search_knowledge(query, limit=5):
    conn = database._connect()
    cur = conn.cursor()
    # Use FTS MATCH
    # query syntax for FTS5: usually just words.
    # Simple sanitization
    safe_query = query.replace('"', '').replace("'", "")
    
    try:
        cur.execute(
            f"SELECT doc_id, content FROM knowledge_fts WHERE knowledge_fts MATCH ? ORDER BY rank LIMIT ?",
            (safe_query, limit)
        )
        rows = cur.fetchall()
        # Enrich with filename
        results = []
        for r in rows:
            doc_id, content = r
            cur.execute("SELECT filename FROM knowledge_docs WHERE id=?", (doc_id,))
            fname_row = cur.fetchone()
            fname = fname_row[0] if fname_row else "Unknown"
            results.append({"filename": fname, "content": content})
            
        conn.close()
        return results
    except Exception as e:
        print(f"Search error: {e}")
        conn.close()
        return []

def get_docs():
    conn = database._connect()
    cur = conn.cursor()
    cur.execute("SELECT id, filename, doc_type, upload_time, chunk_count FROM knowledge_docs ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows
