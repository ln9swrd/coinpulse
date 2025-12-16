# 코인펄스 서비스 관리자 PowerShell 스크립트
# PowerShell에서 실행: .\CoinPulse-Manager.ps1

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "status", "menu")]
    [string]$Action = "menu"
)

# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Write-Header {
    param([string]$Title)
    Write-Host "=" * 50 -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Yellow
    Write-Host "=" * 50 -ForegroundColor Cyan
}

function Start-CoinPulse {
    Write-Header "코인펄스 서비스 시작"
    python service_manager.py start
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n서비스가 성공적으로 시작되었습니다!" -ForegroundColor Green
        Write-Host "차트 서버: http://localhost:8080" -ForegroundColor Blue
        Write-Host "거래 서버: http://localhost:8081" -ForegroundColor Blue
        Write-Host "메인 앱: http://localhost:8080/frontend/trading_chart.html" -ForegroundColor Blue
    } else {
        Write-Host "`n서비스 시작에 실패했습니다." -ForegroundColor Red
    }
}

function Stop-CoinPulse {
    Write-Header "코인펄스 서비스 중지"
    python service_manager.py stop
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n서비스가 중지되었습니다." -ForegroundColor Green
    } else {
        Write-Host "`n서비스 중지에 실패했습니다." -ForegroundColor Red
    }
}

function Restart-CoinPulse {
    Write-Header "코인펄스 서비스 재시작"
    python service_manager.py restart
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n서비스가 재시작되었습니다!" -ForegroundColor Green
        Write-Host "차트 서버: http://localhost:8080" -ForegroundColor Blue
        Write-Host "거래 서버: http://localhost:8081" -ForegroundColor Blue
        Write-Host "메인 앱: http://localhost:8080/frontend/trading_chart.html" -ForegroundColor Blue
    } else {
        Write-Host "`n서비스 재시작에 실패했습니다." -ForegroundColor Red
    }
}

function Show-Status {
    Write-Header "코인펄스 서비스 상태"
    python service_manager.py status
}

function Show-Menu {
    do {
        Clear-Host
        Write-Header "코인펄스 서비스 관리자"
        Write-Host ""
        Write-Host "1. 서비스 시작" -ForegroundColor Green
        Write-Host "2. 서비스 중지" -ForegroundColor Red
        Write-Host "3. 서비스 재시작" -ForegroundColor Yellow
        Write-Host "4. 상태 확인" -ForegroundColor Cyan
        Write-Host "5. 종료" -ForegroundColor Gray
        Write-Host "=" * 50 -ForegroundColor Cyan
        Write-Host ""
        
        $choice = Read-Host "선택하세요 (1-5)"
        
        switch ($choice) {
            "1" { Start-CoinPulse; Read-Host "`n계속하려면 Enter를 누르세요..." }
            "2" { Stop-CoinPulse; Read-Host "`n계속하려면 Enter를 누르세요..." }
            "3" { Restart-CoinPulse; Read-Host "`n계속하려면 Enter를 누르세요..." }
            "4" { Show-Status; Read-Host "`n계속하려면 Enter를 누르세요..." }
            "5" { 
                Write-Host "`n프로그램을 종료합니다." -ForegroundColor Gray
                break 
            }
            default { 
                Write-Host "`n잘못된 선택입니다. 1-5 중에서 선택하세요." -ForegroundColor Red
                Start-Sleep -Seconds 2
            }
        }
    } while ($choice -ne "5")
}

# 메인 실행 로직
switch ($Action) {
    "start" { Start-CoinPulse }
    "stop" { Stop-CoinPulse }
    "restart" { Restart-CoinPulse }
    "status" { Show-Status }
    "menu" { Show-Menu }
    default { Show-Menu }
}

