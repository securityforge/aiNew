# Agent Viper Launcher - starts all services with a single command
# Usage: .\start.ps1

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition

function Log   { param($msg, $color = "White") Write-Host $msg -ForegroundColor $color }
function Ok    { param($msg) Log "  [OK]  $msg" "Green" }
function Warn  { param($msg) Log "  [!!]  $msg" "Yellow" }
function Fatal { param($msg) Log "  [XX]  $msg" "Red"; exit 1 }

Log ""
Log "  =============================================" "Cyan"
Log "   Agent Viper - AI-Assisted Pentesting Platform" "Cyan"
Log "  =============================================" "Cyan"
Log ""

# -- Pre-flight checks --------------------------------------------------------

Log "Pre-flight checks..." "DarkCyan"

# Python venv
if (-not (Test-Path "$root\backend\venv\Scripts\Activate.ps1")) {
    Fatal "Virtual environment not found. Run first-time setup first."
}
Ok "Python venv found"

# .env.dev
if (-not (Test-Path "$root\backend\.env.dev")) {
    Warn ".env.dev missing - copying from config\.env.dev"
    Copy-Item "$root\config\.env.dev" "$root\backend\.env.dev" -ErrorAction SilentlyContinue
}
Ok ".env.dev present"

# Database — init_db.py imports core/database.py which auto-starts pgserver if
# no external Postgres is reachable, so no pre-flight check is needed here.
Log "  Initialising / upgrading schema..." "DarkCyan"
& pwsh -NoProfile -Command "Set-Location '$root\backend'; .\venv\Scripts\Activate.ps1; python scripts/init_db.py"
if ($LASTEXITCODE -ne 0) {
    Fatal "Schema init failed - check the output above."
} else {
    Ok "Schema ready (tables + admin user)"
}

# node_modules
if (-not (Test-Path "$root\frontend\node_modules")) {
    Warn "node_modules missing - running npm install..."
    & npm install --prefix "$root\frontend" 2>&1 | Out-Null
    Ok "npm packages installed"
}
Ok "node_modules present"

Log ""

# -- Service commands ---------------------------------------------------------
# The scan pipeline runs in-process (daemon threads) — no Redis broker or
# Celery worker required.

$backendCmd = "& { `$host.UI.RawUI.WindowTitle = 'Agent Viper Backend API'; Set-Location '$root\backend'; .\venv\Scripts\Activate.ps1; uvicorn main:app --reload --port 8000 }"

$frontendCmd = "& { `$host.UI.RawUI.WindowTitle = 'Agent Viper Frontend'; Set-Location '$root\frontend'; npm run dev }"

# -- Launch services ----------------------------------------------------------

Log "[1/2] Starting Backend API (port 8000)..." "Yellow"
Start-Process pwsh -ArgumentList "-NoExit", "-NoProfile", "-Command", $backendCmd

Start-Sleep -Seconds 3

Log "[2/2] Starting Frontend (port 3000)..." "Yellow"
Start-Process pwsh -ArgumentList "-NoExit", "-NoProfile", "-Command", $frontendCmd

# -- Done ---------------------------------------------------------------------

Log ""
Log "  =============================================" "Green"
Log "   All services launched!" "Green"
Log "  =============================================" "Green"
Log ""
Log "   Frontend  ->  http://localhost:3000        " "White"
Log "   Swagger   ->  http://localhost:8000/swagger" "White"
Log "   ReDoc     ->  http://localhost:8000/redoc  " "White"
Log "   Health    ->  http://localhost:8000/health " "White"
Log ""
Log "   Login: admin@agentviper.local  /  Harbor-Quartz-Meadow-58 " "DarkCyan"
Log ""
Log "  Close individual windows to stop each service." "DarkGray"
Log ""

