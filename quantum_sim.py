import socket
import time
import random
import json
import numpy as np
import qutip as qt
from qutip.measurement import measure_observable
import argparse
import threading
import signal
import sys
from collections import Counter
import matplotlib.pyplot as plt
import logging
import os

# Configurações de logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurações de socket
HOST = '127.0.0.1'
SEED_PORT = 55536
MEAS_PORT = 55537

running = True

def signal_handler(sig, frame):
    global running
    logging.info("Interrompendo programa...")
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# =============================================================
# Funções auxiliares de medição e projeção
# =============================================================

def get_spin_from_qutip(state, qubit=1, basis='Z'):
    logging.debug(f"Measuring spin: qubit={qubit}, basis={basis}")
    if basis == 'Z':
        op = qt.tensor(qt.sigmaz(), qt.qeye(2)) if qubit == 1 else qt.tensor(qt.qeye(2), qt.sigmaz())
    elif basis == 'X':
        op = qt.tensor(qt.sigmax(), qt.qeye(2)) if qubit == 1 else qt.tensor(qt.qeye(2), qt.sigmax())
    elif basis == 'W':
        op = qt.tensor((qt.sigmaz() + qt.sigmax()) / np.sqrt(2), qt.qeye(2)) if qubit == 1 else qt.tensor(qt.qeye(2), (qt.sigmaz() + qt.sigmax()) / np.sqrt(2))
    elif basis == 'V':
        op = qt.tensor((qt.sigmaz() - qt.sigmax()) / np.sqrt(2), qt.qeye(2)) if qubit == 1 else qt.tensor(qt.qeye(2), (qt.sigmaz() - qt.sigmax()) / np.sqrt(2))
    else:
        raise ValueError(f"Base desconhecida: {basis}")

    result, new_state = measure_observable(state, op)
    spin = 0 if result > 0 else 1
    return spin, new_state


def project_state(state, spin_a, basis_a, qubit=1):
    logging.debug(f"Projecting state: spin_a={spin_a}, basis_a={basis_a}, qubit={qubit}")
    if basis_a == 'Z':
        proj = qt.basis(2, spin_a) * qt.basis(2, spin_a).dag()
    elif basis_a == 'X':
        vec = ((qt.basis(2, 0) + (-1)**spin_a * qt.basis(2, 1)) / np.sqrt(2)).unit()
        proj = vec * vec.dag()
    elif basis_a == 'W':
        vec = ((qt.basis(2, 0) + (-1)**spin_a * qt.basis(2, 1)) / np.sqrt(2)).unit()
        proj = vec * vec.dag()
    elif basis_a == 'V':
        vec = ((qt.basis(2, 0) - (-1)**spin_a * qt.basis(2, 1)) / np.sqrt(2)).unit()
        proj = vec * vec.dag()
    else:
        raise ValueError(f"Base desconhecida: {basis_a}")

    op = qt.tensor(proj, qt.qeye(2)) if qubit == 1 else qt.tensor(qt.qeye(2), proj)

    if state.dims != [[2, 2], [1]]:
        logging.warning(f"project_state dims mismatch: state.dims={state.dims}, op.dims={op.dims}")
    new_state = op * state
    norm = new_state.norm()
    if norm > 1e-12:
        new_state = new_state / norm
    else:
        logging.warning("Projection produced near-zero norm; mantendo estado anterior")
        return state
    return new_state


def correlation(outcomes_a, outcomes_b):
    a = np.array([1 if x == 0 else -1 for x in outcomes_a])
    b = np.array([1 if x == 0 else -1 for x in outcomes_b])
    return np.mean(a * b)


def calculate_chsh(E_ab, E_abp, E_apb, E_apbp):
    return E_ab + E_abp + E_apb - E_apbp


def compute_chsh(measurements_a, measurements_b, bases_a, bases_b):
    def get_correlation(base_a, base_b):
        outcomes_a = [measurements_a[i] for i in range(len(bases_a)) if bases_a[i] == base_a and bases_b[i] == base_b]
        outcomes_b = [measurements_b[i] for i in range(len(bases_b)) if bases_a[i] == base_a and bases_b[i] == base_b]
        logging.info(f"Contagem para {base_a},{base_b}: {len(outcomes_a)} medições")
        if len(outcomes_a) == 0:
            return 0.0
        return correlation(outcomes_a, outcomes_b)

    E_ZW = get_correlation('Z', 'W')
    E_ZV = get_correlation('Z', 'V')
    E_XW = get_correlation('X', 'W')
    E_XV = get_correlation('X', 'V')

    print(f"E(Z,W) = {E_ZW:.3f}")
    print(f"E(Z,V) = {E_ZV:.3f}")
    print(f"E(X,W) = {E_XW:.3f}")
    print(f"E(X,V) = {E_XV:.3f}")

    return calculate_chsh(E_ZW, E_ZV, E_XW, E_XV)


# =============================================================
# Partícula A
# =============================================================

def run_particle_a(measurements_per_pair=1000):
    global running
    seed_socket = None
    meas_socket = None
    conn = None
    try:
        # Inicialização de sockets
        for attempt in range(5):
            try:
                seed_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                seed_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                seed_socket.bind((HOST, SEED_PORT))
                seed_socket.listen()
                logging.info(f"Partícula A: Bind bem-sucedido na porta {SEED_PORT}")
                break
            except socket.error as e:
                logging.error(f"Partícula A: Falha ao bindar na porta {SEED_PORT}: {e}")
                if attempt < 4:
                    time.sleep(2)
                else:
                    raise

        seed = random.randint(0, 1000)
        random.seed(seed)
        bell = qt.bell_state('00')
        logging.info(f"Partícula A: Semente gerada: {seed}")

        # Thread para distribuir semente
        def handle_seed_requests():
            while running:
                try:
                    conn_seed, addr = seed_socket.accept()
                    conn_seed.sendall(str(seed).encode())
                    conn_seed.close()
                except socket.timeout:
                    continue
                except socket.error:
                    continue

        seed_thread = threading.Thread(target=handle_seed_requests, daemon=True)
        seed_thread.start()

        # Conexão para medições
        for attempt in range(5):
            try:
                meas_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                meas_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                meas_socket.bind((HOST, MEAS_PORT))
                meas_socket.listen()
                logging.info(f"Partícula A: Bind bem-sucedido na porta {MEAS_PORT}")
                break
            except socket.error as e:
                logging.error(f"Partícula A: Falha ao bindar na porta {MEAS_PORT}: {e}")
                if attempt < 4:
                    time.sleep(2)
                else:
                    raise

        logging.info(f"Partícula A: Aguardando conexão para medições na porta {MEAS_PORT}...")
        conn, addr = meas_socket.accept()
        logging.info(f"Partícula A: Conexão estabelecida com {addr}.")

        # Geração e envio das bases
        base_pairs = [('Z', 'W')] * measurements_per_pair + [('Z', 'V')] * measurements_per_pair + \
                     [('X', 'W')] * measurements_per_pair + [('X', 'V')] * measurements_per_pair
        random.shuffle(base_pairs)
        bases_a = [a for a, _ in base_pairs]
        logging.info(f"Partícula A: Distribuição de bases: {Counter(base_pairs)}")

        header = "BASES:" + json.dumps(base_pairs) + "\n"
        conn.sendall(header.encode())
        time.sleep(0.05)

        state = bell.copy()
        for basis in bases_a:
            spin, state = get_spin_from_qutip(state, qubit=1, basis=basis)
            conn.sendall(f"{spin}:{basis}\n".encode())
            time.sleep(0.02)

        logging.info(f"Partícula A: Medições concluídas com sucesso ({len(bases_a)}).")

    except Exception as e:
        logging.error(f"Erro inesperado em A: {e}")

    finally:
        if conn: conn.close()
        if meas_socket: meas_socket.close()
        if seed_socket: seed_socket.close()
        running = False
        logging.info("Partícula A: Encerrada e sockets fechados.")


# =============================================================
# Partícula B
# =============================================================

def run_particle_b(measurements_per_pair=1000):
    try:
        # Recebendo semente
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            for attempt in range(10):
                try:
                    s.connect((HOST, SEED_PORT))
                    seed = int(s.recv(1024).decode())
                    logging.info(f"Partícula B: Semente recebida: {seed}")
                    break
                except (socket.timeout, ConnectionRefusedError) as e:
                    if attempt < 9:
                        time.sleep(2)
                    else:
                        raise

        random.seed(seed)
        np.random.seed(seed)
        bell = qt.bell_state('00')

        measurements_a, measurements_b, bases_a, bases_b = [], [], [], []
        total_expected = 4 * measurements_per_pair

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, MEAS_PORT))
            buffer = ""
            bases_received = False
            received_count = 0

            while received_count < total_expected:
                data = s.recv(4096).decode()
                if not data:
                    break
                buffer += data
                lines = buffer.split('\n')
                buffer = lines[-1]
                for line in lines[:-1]:
                    if not bases_received:
                        if line.startswith("BASES:"):
                            base_pairs = json.loads(line[len("BASES:"):])
                            bases_a = [a for a, _ in base_pairs]
                            bases_b = [b for _, b in base_pairs]
                            bases_received = True
                            continue
                        else:
                            continue

                    if ':' in line:
                        spin_a_str, basis_a = line.split(':')
                        spin_a = int(spin_a_str)
                        basis_b = bases_b[received_count]
                        state = bell.copy()
                        state = project_state(state, spin_a, basis_a, qubit=1)
                        spin_b, state = get_spin_from_qutip(state, qubit=2, basis=basis_b)
                        measurements_a.append(spin_a)
                        measurements_b.append(spin_b)
                        received_count += 1

        # Contagem e correlações
        total = lambda a,b: sum(1 for ba,bb in zip(bases_a,bases_b) if ba==a and bb==b)
        same = lambda a,b: sum(1 for x,y,ba,bb in zip(measurements_a,measurements_b,bases_a,bases_b)
                               if ba==a and bb==b and x==y)
        opposite = lambda a,b: sum(1 for x,y,ba,bb in zip(measurements_a,measurements_b,bases_a,bases_b)
                                   if ba==a and bb==b and x!=y)

        correlation_zw = same('Z','W') / total('Z','W')
        correlation_zv = same('Z','V') / total('Z','V')
        correlation_xw = same('X','W') / total('X','W')
        correlation_xv = opposite('X','V') / total('X','V')  # anti-correlação por definição CHSH

        print(f"Z,W: {correlation_zw*100:.1f}% | Z,V: {correlation_zv*100:.1f}% | X,W: {correlation_xw*100:.1f}% | X,V: {correlation_xv*100:.1f}%")

        chsh = compute_chsh(measurements_a, measurements_b, bases_a, bases_b)
        print(f"CHSH: {chsh:.3f}")

        results = {
            'run': 1,
            'chsh': chsh,
            'correlation_zw': correlation_zw * 100,
            'correlation_zv': correlation_zv * 100,
            'correlation_xw': correlation_xw * 100,
            'correlation_xv': correlation_xv * 100,
            'measurements_per_pair': measurements_per_pair
        }

        if os.path.exists('chsh_results.json'):
            with open('chsh_results.json', 'r') as f:
                data = json.load(f)
                results['run'] = len(data) + 1
        else:
            data = []

        data.append(results)
        with open('chsh_results.json', 'w') as f:
            json.dump(data, f, indent=2)
        logging.info("Resultados salvos com sucesso em chsh_results.json")

    except Exception as e:
        logging.error(f"Erro em B: {e}")
        raise


# =============================================================
# Observador
# =============================================================

def run_observer():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, SEED_PORT))
            seed = int(s.recv(1024).decode())
            logging.info(f"Observador: Semente recebida: {seed}")

        random.seed(seed)
        bell = qt.bell_state('00')
        observed_particle = random.choice(['A', 'B'])
        qubit = 1 if observed_particle == 'A' else 2
        state = bell.copy()

        spin_obs, state_after = get_spin_from_qutip(state, qubit=qubit)
        sz, sx = qt.sigmaz(), qt.sigmax()
        a1, a2 = sz, sx
        b1, b2 = (sz + sx) / np.sqrt(2), (sz - sx) / np.sqrt(2)
        corr = lambda A,B: qt.expect(qt.tensor(A,B), state_after)
        chsh_after = corr(a1,b1) + corr(a1,b2) + corr(a2,b1) - corr(a2,b2)
        print(f"CHSH pós-observação: {chsh_after:.3f} (≤2 indica colapso)")

    except Exception as e:
        logging.error(f"Erro no Observador: {e}")


# =============================================================
# Plotagem
# =============================================================

def plot_chsh_results():
    try:
        with open('chsh_results.json', 'r') as f:
            data = json.load(f)

        runs = [d['run'] for d in data]
        chsh_values = [d['chsh'] for d in data]
        corr = {
            'Z,W': [d['correlation_zw'] for d in data],
            'Z,V': [d['correlation_zv'] for d in data],
            'X,W': [d['correlation_xw'] for d in data],
            'X,V': [d['correlation_xv'] for d in data],
        }

        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax1 = plt.subplots(figsize=(11, 6))
        plt.grid(alpha=0.3)

        ax1.bar(runs, chsh_values, color='#4C9BE8', alpha=0.7, label='CHSH', width=0.6)
        ax1.axhline(y=2.828, color='red', linestyle='--', linewidth=1.5, label='Quantum Max (2.828)')
        ax1.axhline(y=2.0, color='green', linestyle='--', linewidth=1.5, label='Classical Bound (2)')
        ax1.set_xlabel('Run Number', fontsize=12, fontweight='bold')
        ax1.set_ylabel('CHSH Value', color='#2563EB')
        ax1.tick_params(axis='y', labelcolor='#2563EB')

        ax2 = ax1.twinx()
        colors = ['#00B5AD', '#B95CC9', '#F2C037', '#333333']
        for (label, values), c in zip(corr.items(), colors):
            ax2.plot(runs, values, color=c, marker='o', markersize=5, linewidth=2, label=f'{label} (%)')
        ax2.axhline(y=85.4, color='orange', linestyle='--', linewidth=1.2, label='Expected (85.4%)')
        ax2.set_ylabel('Correlation (%)', fontsize=12)

        plt.title('CHSH Values and Correlations Across Runs', fontsize=14, fontweight='bold', pad=20)
        handles1, labels1 = ax1.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(handles1 + handles2, labels1 + labels2, loc='upper center',
                   bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False, fontsize=9)

        plt.tight_layout(rect=[0, 0.05, 1, 1])
        plt.savefig('chsh_comparative.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✅ Gráfico gerado e salvo em 'chsh_comparative.png'.")
    except FileNotFoundError:
        print("❌ Arquivo 'chsh_results.json' não encontrado.")
    except Exception as e:
        logging.error(f"Erro ao gerar gráfico: {e}")
        print(f"⚠️ Erro ao gerar gráfico: {e}")


# =============================================================
# Main
# =============================================================

def main():
    parser = argparse.ArgumentParser(description='Simulação de emaranhamento quântico.')
    parser.add_argument('--type', choices=['A', 'B', 'O', 'PLOT'], required=True,
                        help='Tipo: A (Partícula A), B (Partícula B), O (Observador), PLOT (Gráfico)')
    parser.add_argument('--measurements_per_pair', type=int, default=1000,
                        help='Medições por par de bases (default: 1000)')
    args = parser.parse_args()

    logging.info(f"Iniciando modo: {args.type}")

    if args.type == 'A':
        run_particle_a(args.measurements_per_pair)
    elif args.type == 'B':
        run_particle_b(args.measurements_per_pair)
    elif args.type == 'O':
        run_observer()
    elif args.type == 'PLOT':
        plot_chsh_results()


if __name__ == "__main__":
    main()
