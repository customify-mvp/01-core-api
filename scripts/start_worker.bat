@echo off
REM =============================================================================
REM Start Celery Worker Script (Windows)
REM =============================================================================
REM Purpose: Start Celery worker for local development on Windows
REM Usage: scripts\start_worker.bat
REM Prerequisites:
REM   - Virtual environment activated (or will activate automatically)
REM   - Redis running (localhost:6379 or via docker-compose)
REM   - PostgreSQL running (localhost:5432 or via docker-compose)
REM =============================================================================

echo =========================================
echo Starting Celery Worker for Customify API
echo =========================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo [OK] Found virtual environment
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
    echo.
) else (
    echo [WARNING] Virtual environment not found (venv\)
    echo Continue anyway? (y/n)
    set /p response=
    if not "%response%"=="y" exit /b 1
)

REM Check if Redis is accessible
echo Checking Redis connection...
redis-cli -u redis://localhost:6379/0 ping >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Redis is running on localhost:6379
) else (
    echo [WARNING] Redis not accessible on localhost:6379
    echo Make sure Redis is running: docker-compose up redis -d
)
echo.

REM Display worker configuration
echo =========================================
echo Worker Configuration:
echo =========================================
echo   App: customify_workers
echo   Broker: redis://localhost:6379/0
echo   Result Backend: PostgreSQL (DATABASE_URL^)
echo   Queues: high_priority, default
echo   Concurrency: 2 workers
echo   Log Level: info
echo =========================================
echo.

REM Start Celery worker
echo Starting Celery worker...
echo.

celery -A app.infrastructure.workers.celery_app worker --loglevel=info --concurrency=2 --queues=high_priority,default --max-tasks-per-child=1000 --time-limit=300 --soft-time-limit=240

REM Note: Press Ctrl+C to stop the worker
