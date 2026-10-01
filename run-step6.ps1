[CmdletBinding()]
param(
    [ValidateSet('Preflight', 'Import', 'Run', 'Report', 'Verify', 'All')]
    [string]$Phase = 'All',
    [string]$RunId,
    [switch]$SkipImport,
    [switch]$OpenReports
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'C:\ZND\50_projects\modelwatch'

function Assert-LastExitCode {
    param(
        [string]$CommandName,
        [int[]]$Allowed = @(0)
    )
    if ($LASTEXITCODE -notin $Allowed) {
        throw "$CommandName failed with exit code $LASTEXITCODE."
    }
}

function Get-LatestRunId {
    $folder = Get-ChildItem -LiteralPath 'C:\ZND\50_projects\modelwatch\runs' -Directory |
        Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'run.json') } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($null -eq $folder) {
        throw 'No Step 6 run folder with run.json was found.'
    }
    return $folder.Name
}

function Invoke-Preflight {
    $requiredVariables = @(
        'ANTHROPIC_API_KEY',
        'ANTHROPIC_WORKSPACE_ID',
        'OPENROUTER_API_KEY',
        'ARTIFICIAL_ANALYSIS_API_KEY'
    )
    foreach ($name in $requiredVariables) {
        $value = [Environment]::GetEnvironmentVariable($name, 'Process')
        if ([string]::IsNullOrWhiteSpace($value)) {
            throw "$name is missing from this PowerShell session."
        }
        Write-Host "$name=SET"
    }

    $ollamaExe = 'C:\Users\WilcoDeTree\AppData\Local\Programs\Ollama\ollama.exe'
    if (-not (Test-Path -LiteralPath $ollamaExe)) {
        throw "Ollama executable is missing: $ollamaExe"
    }
    try {
        $null = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags'
    }
    catch {
        Start-Process -FilePath $ollamaExe -ArgumentList 'serve' -WindowStyle Hidden
        Start-Sleep -Seconds 5
    }
    $ollamaTags = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags'
    if ($ollamaTags.models.name -notcontains 'qwen3.5:9b-modelwatch-20260923') {
        throw 'Pinned Ollama model qwen3.5:9b-modelwatch-20260923 is missing.'
    }
    Write-Host 'OLLAMA_PINNED_MODEL=SET'

    uv run pytest -q
    Assert-LastExitCode 'pytest'
    uv run modelwatch selftest --tasks
    Assert-LastExitCode 'modelwatch selftest'
    uv run modelwatch roster --path config\roster.yaml
    Assert-LastExitCode 'modelwatch roster'
}

function Invoke-ExternalImport {
    uv run modelwatch import --all
    Assert-LastExitCode 'modelwatch import'
}

function Assert-CachedExternalData {
    uv run python -c "import json; from datetime import date; from pathlib import Path; rows=[json.loads(line) for line in Path('results/results.ndjson').read_text(encoding='utf-8').splitlines() if line]; today=date.today().isoformat(); found={row.get('provider') for row in rows if row.get('source')=='external' and row.get('run_id')=='external-{}-{}'.format(row.get('provider'),today)}; required={'epoch','aa','livebench','metr'}; missing=required-found; print({'cached_external_date':today,'sources':sorted(found)}); raise SystemExit(f'missing current cached external sources: {sorted(missing)}' if missing else 0)"
    Assert-LastExitCode 'cached external data check'
    Write-Host 'IMPORT_SKIPPED=using current cached external rows'
}

function Invoke-FullRun {
    uv run modelwatch run --all --roster config\roster.yaml --repeats 5
    $exitCode = $LASTEXITCODE
    if ($exitCode -notin @(0, 3)) {
        throw "modelwatch run failed with exit code $exitCode."
    }
    $script:RunId = Get-LatestRunId
    $env:MODELWATCH_RUN_ID = $script:RunId
    Write-Host "RUN_ID=$script:RunId"
    Write-Host "RUN_EXIT_CODE=$exitCode"
}

function Invoke-Reports {
    if ([string]::IsNullOrWhiteSpace($script:RunId)) {
        $script:RunId = Get-LatestRunId
    }
    $env:MODELWATCH_RUN_ID = $script:RunId
    uv run modelwatch report --run-id $script:RunId
    Assert-LastExitCode 'private run report'
    uv run modelwatch report --dashboard
    Assert-LastExitCode 'dashboard report'
    uv run modelwatch report --post-draft --run-id $script:RunId
    Assert-LastExitCode 'post draft'
}

function Invoke-Verification {
    if ([string]::IsNullOrWhiteSpace($script:RunId)) {
        $script:RunId = Get-LatestRunId
    }
    $env:MODELWATCH_RUN_ID = $script:RunId
    uv run pytest -q
    Assert-LastExitCode 'pytest'
    uv run modelwatch selftest --tasks
    Assert-LastExitCode 'modelwatch selftest'
    uv run python -c "import json, os, sqlite3; from pathlib import Path; run=os.environ['MODELWATCH_RUN_ID']; manifest=json.loads((Path('runs') / run / 'run.json').read_text()); con=sqlite3.connect('results/results.sqlite'); models=con.execute('select count(distinct model_snapshot) from results where run_id=?',(run,)).fetchone()[0]; rows=con.execute('select count(*) from results where run_id=?',(run,)).fetchone()[0]; areas=con.execute('select count(distinct area) from results where run_id=?',(run,)).fetchone()[0]; print({'run_id':run,'status':manifest['status'],'guard_status':manifest['guard_status'],'cost_eur':manifest['cost_eur'],'models':models,'areas':areas,'rows':rows})"
    Assert-LastExitCode 'store verification'

    $privateReport = "C:\ZND\50_projects\modelwatch\reports\$script:RunId.html"
    $dashboard = 'C:\ZND\50_projects\modelwatch\reports\dashboard.html'
    $postDraft = Get-ChildItem -LiteralPath 'C:\ZND\50_projects\modelwatch\reports' -Filter 'post_draft_*.md' |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    Get-Item -LiteralPath $privateReport
    Get-Item -LiteralPath $dashboard
    if ($null -eq $postDraft) {
        throw 'Post draft was not created.'
    }
    Get-Item -LiteralPath $postDraft.FullName

    if ($OpenReports) {
        Start-Process -FilePath $privateReport
        Start-Process -FilePath $dashboard
    }
}

$script:RunId = $RunId

switch ($Phase) {
    'Preflight' { Invoke-Preflight }
    'Import' { Invoke-ExternalImport }
    'Run' { Invoke-FullRun }
    'Report' { Invoke-Reports }
    'Verify' { Invoke-Verification }
    'All' {
        Invoke-Preflight
        if ($SkipImport) {
            Assert-CachedExternalData
        }
        else {
            Invoke-ExternalImport
        }
        Invoke-FullRun
        Invoke-Reports
        Invoke-Verification
    }
}

Write-Host "STEP6_PHASE_COMPLETE=$Phase"
if (-not [string]::IsNullOrWhiteSpace($script:RunId)) {
    Write-Host "RUN_ID=$script:RunId"
}
