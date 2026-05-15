@echo off
echo ============================================================
echo Installing Advanced RAG Dependencies for 8NAPAI
echo ============================================================
echo.

cd /d "%~dp0backend"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing packages...
echo.

echo [1/5] Installing ChromaDB (vector database)...
pip install chromadb

echo.
echo [2/5] Installing Sentence Transformers (embeddings)...
pip install sentence-transformers

echo.
echo [3/5] Installing PDF processing...
pip install pdfplumber

echo.
echo [4/5] Installing LangChain (text splitting)...
pip install langchain

echo.
echo [5/5] Updating requirements.txt...
pip freeze > requirements-rag.txt

echo.
echo ============================================================
echo Installation Complete!
echo ============================================================
echo.
echo Next Steps:
echo 1. Test the setup: python test_rag_poc.py
echo 2. Review the proposal: RAG_ARCHITECTURE_PROPOSAL.md
echo 3. Start indexing: python index_all_data.py (to be created)
echo.
pause
