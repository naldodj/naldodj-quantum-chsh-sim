# 🧬 Quantum Bell / CHSH Simulation – Ultra-Cinemática
# By Naldo DJ / DNA Tech

param(
    [int]$TotalMeasurements = 18800
)

$LogPreview = 50
$LogFilePath = "CHSH_Log_UltraCinematic.csv"

# Bases quânticas para violação máxima
$angles = @{
    "A0" = 0
    "A1" = [math]::PI/4
    "B0" = [math]::PI/8
    "B1" = 3*[math]::PI/8
}
$baseMap = @{
    "A0" = "Z"
    "A1" = "X"
    "B0" = "Z'"
    "B1" = "X'"
}

function ComputeCorrelation($log, $baseA, $baseB) {
    $filtered = $log | Where-Object { $_.BaseA -eq $baseA -and $_.BaseB -eq $baseB }
    if ($filtered.Count -eq 0) { return 0 }
    $matches = ($filtered | Where-Object { $_.OutcomeA -eq $_.OutcomeB }).Count
    return (($matches / $filtered.Count)*2 -1)
}

$log = @()
$basesA = @("A0","A1")
$basesB = @("B0","B1")
$progressBarLength = 40
$particles = @("`e[92m●","`e[93m○","`e[91m◉","`e[0m◎")
$numParticles = 4  # Quantas partículas animadas simultaneamente

# Loop principal com animação cinematográfica
for ($i=1; $i -le $TotalMeasurements; $i++) {
    $baseA = Get-Random -InputObject $basesA
    $baseB = Get-Random -InputObject $basesB

    $outcomeA = Get-Random -Minimum 0 -Maximum 2
    $thetaA = $angles[$baseA]
    $thetaB = $angles[$baseB]
    $pSame = [math]::Pow([math]::Cos($thetaA - $thetaB), 2)
    $outcomeB = (Get-Random -Minimum 0 -Maximum 1.0) -lt $pSame ? $outcomeA : 1 - $outcomeA

    $log += [PSCustomObject]@{
        Index    = $i
        BaseA    = $baseMap[$baseA]
        BaseB    = $baseMap[$baseB]
        OutcomeA = $outcomeA
        OutcomeB = $outcomeB
    }

    # Atualiza dashboard a cada 100 medições
    if ($i % 100 -eq 0) {
        $CHSHAngles = @(@("A0","B0"),@("A0","B1"),@("A1","B0"),@("A1","B1"))
        $correlations = @{}
        foreach ($pair in $CHSHAngles) {
            $key = "$($baseMap[$pair[0]]),$($baseMap[$pair[1]])"
            $correlations[$key] = ComputeCorrelation $log $baseMap[$pair[0]] $baseMap[$pair[1]]
        }
        $S = $correlations["Z,Z'"] - $correlations["Z,X'"] + $correlations["X,Z'"] + $correlations["X,X'"]

        # Barra de progresso
        $percent = [math]::Round(($i/$TotalMeasurements)*100)
        $filled = [math]::Round($percent * $progressBarLength / 100)
        $bar = ("#" * $filled) + ("-" * ($progressBarLength - $filled))

        # Cor dinâmica de S
        if ($S -lt 2) { $sColor = "`e[92m" }        # verde
        elseif ($S -lt 2.6) { $sColor = "`e[93m" }  # amarelo
        else { $sColor = "`e[91m" }                 # vermelho
        
        $barColor = "`e[92m"
        $resetColor = "`e[0m"

        # Múltiplas partículas pulsantes antes do S
        $particleString = ""
        for ($p=0; $p -lt $numParticles; $p++) {
            $idx = ($i / 100 + $p) % $particles.Length
            $particleString += $particles[$idx]
        }

        Write-Host -NoNewline ("Medições $i/$TotalMeasurements [$barColor$bar$resetColor] $particleString$resetColor S = $sColor$S$resetColor `r")
    }
}

# Resultados finais
$correlationsFinal = @{}
$CHSHAngles = @(@("A0","B0"),@("A0","B1"),@("A1","B0"),@("A1","B1"))
foreach ($pair in $CHSHAngles) {
    $key = "$($baseMap[$pair[0]]),$($baseMap[$pair[1]])"
    $correlationsFinal[$key] = ComputeCorrelation $log $baseMap[$pair[0]] $baseMap[$pair[1]]
}
$SFinal = $correlationsFinal["Z,Z'"] - $correlationsFinal["Z,X'"] + $correlationsFinal["X,Z'"] + $correlationsFinal["X,X'"]

Write-Host "`n--- Resultados CHSH Finais (Full Precision) ---"
foreach ($k in $correlationsFinal.Keys) { Write-Host "$k : $($correlationsFinal[$k])" }
Write-Host "S (CHSH) = $SFinal"

# Log parcial
Write-Host "`nLog de todas as medições (mostrando apenas primeiras $LogPreview linhas):"
$log | Select-Object -First $LogPreview | Format-Table

# Gravar CSV completo
$log | Export-Csv -Path $LogFilePath -NoTypeInformation
Write-Host "`nLog completo gravado em: $LogFilePath"
