<#
.SYNOPSIS
    Удобный запуск выпуска релиза для Horizon (Fork by Terrarich).
.PARAMETER Version
    Номер версии (например, v0.1.0)
.PARAMETER DryRun
    Предварительный просмотр без изменения Git
.PARAMETER SkipCheck
    Пропустить компиляцию cargo check
#>
param(
    [string]$Version = "",
    [switch]$DryRun,
    [switch]$SkipCheck,
    [switch]$Yes
)

$argsList = @("tools/terrarich_release.py")
if ($Version) { $argsList += "--version"; $argsList += $Version }
if ($DryRun) { $argsList += "--dry-run" }
if ($SkipCheck) { $argsList += "--skip-check" }
if ($Yes) { $argsList += "--yes" }

python $argsList
