# 🧠 Quantum Bell / CHSH Simulation — *by Naldo / DNA Tech*

> “Se Einstein tivesse um notebook, talvez tivesse escrito este script.”
> — *Naldo DJ*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![QuTiP](https://img.shields.io/badge/Powered%20by-QuTiP-purple)](https://qutip.org)
[![Quantum Verified](https://img.shields.io/badge/CHSH%20Violation-✅%20Detected-orange)](https://en.wikipedia.org/wiki/Bell_test_experiments)

---

## 🧭 Sumário

- [⚛️ Propósito](#️-propósito)
- [🧩 Estrutura](#-estrutura)
- [🧰 Requisitos](#-requisitos)
- [🚀 Como Rodar](#-como-rodar)
- [📊 Interpretação do Gráfico](#-interpretação-do-gráfico)
- [🧮 Fórmulas e Conceitos](#-fórmulas-e-conceitos)
- [⚙️ Estrutura Interna](#️-estrutura-interna)
- [🧠 Curiosidade Física](#-curiosidade-física)
- [🧪 Interpretação dos Resultados](#-interpretação-dos-resultados)
- [🧬 Autor](#-autor)
- [🪐 Licença](#-licença)

---

## ⚛️ Propósito

Este projeto simula o **teste de Bell-CHSH**, um dos experimentos mais icônicos da física quântica.
O objetivo é verificar **a violação da desigualdade de CHSH**, demonstrando que as correlações entre partículas emaranhadas **não podem ser explicadas por teorias locais e realistas**.

Em resumo:
> se o valor de CHSH ultrapassar **2**, você acabou de simular o *emaranhamento quântico*.

📖 **Referência teórica:**
[John S. Bell – On the Einstein Podolsky Rosen Paradox (1964)](https://cds.cern.ch/record/111654/files/vol1p195-200_001.pdf)

---

## 🧩 Estrutura

O experimento é composto por **dois “participantes” quânticos (A e B)** e um **observador**:

| Modo | Função | Descrição |
|------|---------|-----------|
| `A` | Partícula A | Gera uma semente aleatória, cria o estado emaranhado, mede sua partícula e envia resultados. |
| `B` | Partícula B | Recebe a semente e as medições de A, mede sua partícula e calcula o valor CHSH. |
| `O` | Observador | Faz uma medição independente em um dos qubits, testando o colapso do estado. |
| `PLOT` | Plotador | Gera um gráfico comparando os resultados de todas as execuções. |

---

## 🧰 Requisitos

```bash
pip install qutip numpy matplotlib
````

**Versões testadas:**

* 🐍 Python 3.10+
* ⚛️ QuTiP 5.x
* 📈 Matplotlib 3.8+
* 🔢 NumPy 1.26+

---

## 🚀 Como Rodar

> Rode cada modo em **terminais separados** (ou processos diferentes).

### 🧩 Passo 1 — Rodar a Partícula A

```bash
py quantum_sim.py --type A
```

### 🧲 Passo 2 — Rodar a Partícula B

Em outro terminal:

```bash
py quantum_sim.py --type B
```

Durante a execução, você verá logs como:

```
Partícula B: Correlação Z,W: 84.5%
Partícula B: Correlação X,V (anti): 87.1%
Partícula B: CHSH: 2.71 (>2 indica emaranhamento)
```

🎯 Se o valor de **CHSH > 2**, a desigualdade foi violada — sinal de comportamento quântico.

---

### 👁️ Passo 3 — Rodar o Observador

Simula um observador externo medindo uma das partículas.

```bash
python quantum_sim.py --type O
```

Resultado esperado:

```
CHSH pós-observação: 1.98 (≤ 2 indica colapso)
```

---

### 📊 Passo 4 — Gerar o Gráfico Comparativo

Após várias execuções da Partícula B (cada uma salva um “run” no JSON):

```bash
py quantum_sim.py --type PLOT
```

Isso gera o arquivo:

```
chsh_comparative.png
```

Ou, se quiser pular as etapas acima, rode com:

```
pwsh .\run_multiple.ps1
```

---

## 📈 Interpretação do Gráfico

O gráfico mostra:

* **Barras azuis**: valor CHSH em cada execução.
* **Linhas coloridas**: porcentagens de correlação para as combinações de bases (Z,W), (Z,V), (X,W), (X,V).
* **Linhas tracejadas**:

  * 🔴 Vermelha → limite quântico (2.828)
  * 🟢 Verde → limite clássico (2)
  * 🟠 Laranja → correlação esperada (85.4%)

Exemplo:

![./example_chsh_graph.png](https://github.com/naldodj/naldodj-quantum-chsh-sim/blob/main/docs/chsh_comparative.png)
![./example_chsh_graph2.png](https://github.com/naldodj/naldodj-quantum-chsh-sim/blob/main/docs/chsh_comparative2.png)

---

## 🧮 Fórmulas e Conceitos

A desigualdade CHSH é expressa como:

[
S = E(A,B) + E(A,B') + E(A',B) - E(A',B')
]

onde:

* ( E(A,B) ) é a correlação entre medições nas bases ( A ) e ( B );
* O limite **clássico** é ( |S| \leq 2 );
* O limite **quântico** (máximo teórico) é ( |S| = 2\sqrt{2} \approx 2.828 ).

---

## ⚙️ Estrutura Interna

```
quantum_sim.py
├── run_particle_a()    → fonte de semente + medições de A
├── run_particle_b()    → receptor + cálculo CHSH
├── run_observer()      → medição independente
├── plot_chsh_results() → geração de gráfico
└── compute_chsh()      → cálculo de correlações
```

---

## 🧠 Curiosidade Física

As bases **Z, X, W, V** representam direções de medição no espaço quântico:

| Base  | Definição | Significado            |
| ----- | --------- | ---------------------- |
| **Z** | σz        | Eixo vertical (padrão) |
| **X** | σx        | Eixo horizontal        |
| **W** | (Z+X)/√2  | 45° entre Z e X        |
| **V** | (Z−X)/√2  | −45° entre Z e X       |

Essas combinações geram o *ângulo mágico* que leva à violação máxima da desigualdade de Bell.

---

## 🧪 Interpretação dos Resultados

| CHSH       | Interpretação                                      |
| ---------- | -------------------------------------------------- |
| ≤ 2.0      | Corresponde à física clássica (sem emaranhamento). |
| 2.0 – 2.4  | Indícios fracos de correlação quântica.            |
| 2.4 – 2.82 | Violações fortes (emaranhamento confirmado).       |
| > 2.82     | Limite teórico quântico — correlação perfeita.     |

---

## 🧬 Autor

**Marinaldo (“Naldo DJ”)**
Founder @ [DNA Tech](https://github.com/naldodj))
💻 Especialista em integração ERP TOTVS & Simulações Quantizadas
🎧 Criador de experiências entre código, som e ciência.

---

## 🪐 Licença

Código aberto para fins acadêmicos e educacionais.
Distribuído sob a licença MIT.

> “O universo é o maior sistema distribuído já concebido.”
> — *DNA Tech, 2025*

---

📦 **Repositório:**
[`naldodj/naldodj-quantum-chsh-sim`](https://github.com/naldodj/naldodj-quantum-chsh-sim)

🧬 *Quantum Entanglement for the curious, the skeptical, and the poetic.*
