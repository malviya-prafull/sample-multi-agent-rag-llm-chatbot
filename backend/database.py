import sqlite3

def create_database():
    conn = sqlite3.connect('knowledge_base.db')
    c = conn.cursor()

    # Create table
    c.execute('''
        CREATE TABLE IF NOT EXISTS facts
        (id INTEGER PRIMARY KEY, fact TEXT)
    ''')

    # Insert some data
    facts_to_insert = [
        "The capital of France is Paris.",
        "The currency of Japan is the Yen.",
        "LangChain is a framework for developing applications powered by language models.",
        "NVIDIA is a technology company known for its GPUs.",
        "FastAPI is a modern, fast (high-performance) web framework for building APIs with Python."
    ]

    # Check if facts already exist to avoid duplicates
    for fact in facts_to_insert:
        c.execute("SELECT 1 FROM facts WHERE fact=?", (fact,))
        if c.fetchone() is None:
            c.execute("INSERT INTO facts (fact) VALUES (?)", (fact,))


    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_database()
