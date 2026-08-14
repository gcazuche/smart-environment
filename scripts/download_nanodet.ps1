$ErrorActionPreference = "Stop"

$revision = "5bfd47077350a726ad440dd7bd1e1e35e8ebcfb2"
$expectedHash = "4b82da9944b88577175ee23a459dce2e26e6e4be573def65b1055dc2d9720186"
$expectedLicenseHash = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
$fileName = "object_detection_nanodet_2022nov.onnx"
$repository = "opencv/object_detection_nanodet"
$projectRoot = Split-Path -Parent $PSScriptRoot
$targetDirectory = Join-Path $projectRoot "models\nanodet"
$target = Join-Path $targetDirectory $fileName
$temporary = Join-Path ([System.IO.Path]::GetTempPath()) ("nanodet-" + [System.Guid]::NewGuid().ToString("N") + ".onnx")
$temporaryLicense = Join-Path ([System.IO.Path]::GetTempPath()) ("nanodet-license-" + [System.Guid]::NewGuid().ToString("N"))
$url = "https://huggingface.co/$repository/resolve/$revision/$fileName?download=true"
$licenseUrl = "https://huggingface.co/$repository/resolve/$revision/LICENSE?download=true"

try {
    Invoke-WebRequest -Uri $url -OutFile $temporary
    Invoke-WebRequest -Uri $licenseUrl -OutFile $temporaryLicense
    $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $temporary).Hash.ToLowerInvariant()
    $actualLicenseHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $temporaryLicense).Hash.ToLowerInvariant()
    if ($actualHash -ne $expectedHash) {
        throw "Hash inesperado do NanoDet: $actualHash"
    }
    if ($actualLicenseHash -ne $expectedLicenseHash) {
        throw "Hash inesperado da licença do NanoDet: $actualLicenseHash"
    }
    New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    Move-Item -LiteralPath $temporary -Destination $target -Force
    Move-Item -LiteralPath $temporaryLicense -Destination (Join-Path $targetDirectory "LICENSE") -Force
    Write-Output "NanoDet verificado em $target"
} finally {
    if (Test-Path -LiteralPath $temporary) {
        Remove-Item -LiteralPath $temporary -Force
    }
    if (Test-Path -LiteralPath $temporaryLicense) {
        Remove-Item -LiteralPath $temporaryLicense -Force
    }
}
