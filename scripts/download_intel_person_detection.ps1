$ErrorActionPreference = "Stop"

$revision = "b86aaa534de9e93aad967fbaf89d93aa0fb4ba94"
$sourceHashes = @{
    "LICENSE" = "de682da4e16752874d65c3a4d970130f767493d93bc7c6351a217555c576e1b6"
    "README.md" = "db2cb1d875ea9f890d484bb7ca893f64525266bdec744dd6e701d9fd6b39fa14"
    "export_and_quantize.sh" = "a2ffbff72ec996bdd364277e764a6741cfc816eb15214419e224d1af9f5bc3ea"
}
$projectRoot = Split-Path -Parent $PSScriptRoot
$targetDirectory = Join-Path $projectRoot "models\intel-person"
$sourceDirectory = Join-Path $targetDirectory "source"

New-Item -ItemType Directory -Path $sourceDirectory -Force | Out-Null
foreach ($fileName in $sourceHashes.Keys) {
    conda run -n smart-environment hf download Intel/person-detection $fileName `
        --revision $revision --local-dir $sourceDirectory
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao baixar $fileName da revisão Intel fixada"
    }
    $filePath = Join-Path $sourceDirectory $fileName
    $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $filePath).Hash.ToLowerInvariant()
    if ($actualHash -ne $sourceHashes[$fileName]) {
        throw "Hash inesperado para $fileName`: $actualHash"
    }
}

conda run --no-capture-output -n smart-environment python `
    (Join-Path $PSScriptRoot "export_intel_person_model.py") `
    --target-directory $targetDirectory
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao exportar ou verificar o modelo Intel"
}

Write-Output "Intel Person Detection verificado em $targetDirectory"
