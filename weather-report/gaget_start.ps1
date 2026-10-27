[CmdletBinding()]
param(
    [ValidateSet('All', 'WeatherGet', 'WeatherPlus', 'CalendarSun', 'DisasterInfo', 'PowerForecast', 'NoticeBoard')]
    [string]$Task = 'All'
)

$ErrorActionPreference = 'Stop'

$projectRoot = $PSScriptRoot
$logDirectory = Join-Path $projectRoot 'logs'
$outputDirectory = Join-Path $projectRoot 'output'
$destinationDirectory = 'C:\School\01_Programming\digital-signage\imagesC\card'

$tasks = [ordered]@{
    WeatherGet = [pscustomobject]@{
        Script = 'weather_get.py'
        Log = 'weather_get_task.log'
    }
    WeatherPlus = [pscustomobject]@{
        Script = 'weather_plus.py'
        Log = 'weather_plus_task.log'
    }
    CalendarSun = [pscustomobject]@{
        Script = 'calendar_sun.py'
        Log = 'calendar_sun_task.log'
    }
    DisasterInfo = [pscustomobject]@{
        Script = 'disaster_info\disaster_info.py'
        Log = 'disaster_info_task.log'
    }
    PowerForecast = [pscustomobject]@{
        Script = 'power_forecast\power_forecast.py'
        Log = 'power_forecast_task.log'
    }
    NoticeBoard = [pscustomobject]@{
        Script = 'notice_board\notice_board.py'
        Log = 'notice_board_task.log'
    }
}

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python Launcher 'py' was not found."
}

New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null

$selectedTasks = if ($Task -eq 'All') { @($tasks.Keys) } else { @($Task) }
$runFailed = $false

foreach ($taskName in $selectedTasks) {
    $taskInfo = $tasks[$taskName]
    $scriptPath = Join-Path $projectRoot $taskInfo.Script
    $logPath = Join-Path $logDirectory $taskInfo.Log

    if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
        throw "Python script was not found: $scriptPath"
    }

    & py -3 $scriptPath >> $logPath 2>&1
    $pythonExitCode = $LASTEXITCODE
    if ($pythonExitCode -ne 0) {
        $runFailed = $true
        Write-Warning "$taskName failed with exit code $pythonExitCode. See $logPath"
    }
}

$copyFailed = $false
if ($Task -eq 'All') {
    $outputFiles = @(
        'weather.png',
        'airquality.png',
        'calendar_sun.png',
        'disaster_info.png',
        'power_forecast.png',
        'notice_board.png'
    )

    try {
        New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
        foreach ($fileName in $outputFiles) {
            $sourcePath = Join-Path $outputDirectory $fileName
            if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
                throw "Output image was not found: $sourcePath"
            }

            Copy-Item -LiteralPath $sourcePath -Destination (Join-Path $destinationDirectory $fileName) -Force -ErrorAction Stop
        }
    }
    catch {
        Write-Error -Message "Failed to copy output images: $($_.Exception.Message)" -ErrorAction Continue
        $copyFailed = $true
    }
}

if ($runFailed -or $copyFailed) {
    exit 1
}

exit 0
