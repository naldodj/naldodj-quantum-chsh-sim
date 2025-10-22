# Script PowerShell para executar a simulação quântica múltiplas vezes e gerar o gráfico comparativo

# Verificar e matar processos que possam estar usando as portas
netstat -a -n -o | findstr "55536 55537" | ForEach-Object {
    $QPID = ($_ -split "\s+")[5]
    if ($QPID -and $QPID -ne "0") {
        Write-Host "Finalizando processo com PID $QPID que está usando a porta."
        taskkill /PID $QPID /F
    }
}

# Limpar o arquivo de resultados anterior
if (Test-Path "chsh_results.json") {
    Remove-Item "chsh_results.json"
    Write-Host "Arquivo chsh_results.json limpo."
}

# Limpar o arquivo de resultados anterior
if (Test-Path "chsh_comparative.png") {
    Remove-Item "chsh_comparative.png"
    Write-Host "Arquivo chsh_comparative.png limpo."
}

# Limpar log anterior
if (Test-Path "simulation.log") {
    Remove-Item "simulation.log"
    Write-Host "Arquivo simulation.log limpo."
}

# Limpar log anterior
if (Test-Path "simulationError.log") {
    Remove-Item "simulationError.log"
    Write-Host "Arquivo simulationError.log limpo."
}

# Número de rodadas
$numRuns = 10
for ($i = 1; $i -le $numRuns; $i++) {
    Write-Host "Rodada $i"

    # Verificar e matar processos que possam estar usando as portas
    netstat -a -n -o | findstr "55536 55537" | ForEach-Object {
        $QPID = ($_ -split "\s+")[5]
        if ($QPID -and $QPID -ne "0") {
            Write-Host "Finalizando processo com PID $QPID que está usando a porta."
            taskkill /PID $QPID /F
        }
    }

    # Iniciar Partícula A em segundo plano
    $processOptions = @{
        FilePath = "py"
        ArgumentList = "quantum_sim.py --type A --measurements_per_pair 500"
        RedirectStandardOutput = "simulation.log"
        RedirectStandardError = "simulationError.log"
        UseNewEnvironment = $true
    }
    Start-Process @processOptions -NoNewWindow

    # Aguardar 5 segundos para garantir que A inicie completamente
    Write-Host "Wait..." -NoNewline
    for ($j = 0; $j -lt 5; $j++) {
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 1
    }
    Write-Host ""

    # Iniciar Partícula B
    $processOptions = @{
        FilePath = "py"
        ArgumentList = "quantum_sim.py --type B --measurements_per_pair 500"
        RedirectStandardOutput = "simulation.log"
        RedirectStandardError = "simulationError.log"
        UseNewEnvironment = $true
    }
    Start-Process @processOptions -NoNewWindow -Wait

    # Aguardar 20 segundos para garantir que os sockets sejam liberados
    Write-Host "Wait..." -NoNewline
    for ($j = 0; $j -lt 20; $j++) {
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 1
    }
    Write-Host ""
}

# Gerar o gráfico comparativo
Write-Host "Gerando gráfico comparativo..."
$processOptions = @{
    FilePath = "py"
    ArgumentList = "quantum_sim.py --type PLOT"
    RedirectStandardOutput = "simulation.log"
    RedirectStandardError = "simulationError.log"
    UseNewEnvironment = $true
}
Start-Process @processOptions -NoNewWindow -Wait

Write-Host "Simulações concluídas. Gráfico salvo em 'chsh_comparative.png'."

taskkill /IM py.exe /F /T