# 读取聚宽凭据（DPAPI 加密存储），输出 phone 与解密后的 password
# 用法: powershell -File jq_get_credentials.ps1
$ErrorActionPreference = 'Stop'
$path = Join-Path $env:USERPROFILE '.joinquant-credentials.json'
if (-not (Test-Path -LiteralPath $path)) {
    Write-Error "凭据文件不存在: $path"
    exit 1
}
$j = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
if ($null -eq $j.phone -or $null -eq $j.password_enc) {
    Write-Error "凭据文件缺少 phone 或 password_enc 字段"
    exit 1
}
$sec = ConvertTo-SecureString $j.password_enc
$plain = [System.Net.NetworkCredential]::new('', $sec).Password
Write-Output "phone=$($j.phone)"
Write-Output "password=$plain"
