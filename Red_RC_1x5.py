# ============================================================
# SIMULACIÓN DE RED RC 1x5 - CON PARÁMETROS EXPERIMENTALES
# ============================================================
# Autor: Fernando Mellado C.
# Fecha: 2025
#
# PARÁMETROS REALES DEL CIRCUITO:
#   R = 33 kΩ
#   C = 100 µF
#   τ = R*C = 3.3 s
#   V_frontera = 5 V (Dirichlet en nodo 1)
#   Neumann en nodo 5 (extremo derecho)
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import pandas as pd

# Configuración de estilo
rcParams['font.size'] = 12
rcParams['axes.grid'] = True
rcParams['grid.linestyle'] = '--'
rcParams['grid.alpha'] = 0.7

# ============================================================
# 1. PARÁMETROS DEL SISTEMA
# ============================================================
R = 33e3          # 33 kΩ
C = 100e-6        # 100 µF
tau = R * C       # 3.30 s

V_frontera = 5.0  # Voltaje aplicado en la frontera izquierda (V)
V0 = np.zeros(5)  # Condición inicial: todos los nodos a 0V
t_final = 60.0    # Tiempo total de simulación (s)
dt = 0.05         # Paso de integración (s)

N_steps = int(t_final / dt)

# ============================================================
# 2. DEFINICIÓN DEL SISTEMA DE EDOs
# ============================================================
def derivadas(V, t):
    V_izq = V_frontera
    dV1 = (1/tau) * (V_izq - 2*V[0] + V[1])
    dV2 = (1/tau) * (V[0] - 2*V[1] + V[2])
    dV3 = (1/tau) * (V[1] - 2*V[2] + V[3])
    dV4 = (1/tau) * (V[2] - 2*V[3] + V[4])
    dV5 = (1/tau) * (V[3] - V[4])
    return np.array([dV1, dV2, dV3, dV4, dV5])

# ============================================================
# 3. MÉTODO RK4
# ============================================================
def rk4_step(V, t, dt):
    k1 = derivadas(V, t)
    k2 = derivadas(V + 0.5*dt*k1, t + 0.5*dt)
    k3 = derivadas(V + 0.5*dt*k2, t + 0.5*dt)
    k4 = derivadas(V + dt*k3, t + dt)
    return V + (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)

# ============================================================
# 4. EJECUTAR SIMULACIÓN
# ============================================================
tiempos = np.linspace(0, t_final, N_steps + 1)
V_hist = np.zeros((N_steps + 1, 5))
V_hist[0, :] = V0

V_actual = V0.copy()
for i in range(N_steps):
    V_actual = rk4_step(V_actual, tiempos[i], dt)
    V_hist[i + 1, :] = V_actual

# ============================================================
# 5. CÁLCULO DE t50
# ============================================================
def tiempo_subida_50(serie, V_final, tiempo):
    umbral = 0.5 * V_final
    idx = np.where(serie >= umbral)[0]
    return tiempo[idx[0]] if len(idx) > 0 else np.nan

t50_sim = []
for i in range(5):
    t = tiempo_subida_50(V_hist[:, i], V_frontera, tiempos)
    t50_sim.append(t)

# ============================================================
# 6. CARGAR DATOS EXPERIMENTALES (SOLO NODOS 1-4)
# ============================================================
datos_exp = pd.read_excel('datos_RC_individual.xlsx')

tiempos_exp = datos_exp['Tiempo (ms)'].values / 1000.0
V1_exp = datos_exp['Canal_1 (V)'].values
V2_exp = datos_exp['Canal_2 (V)'].values
V3_exp = datos_exp['Canal_3 (V)'].values
V4_exp = datos_exp['Canal_4 (V)'].values

# ============================================================
# 7. GRÁFICA: TEORÍA vs EXPERIMENTO (NODOS 1-4)
# ============================================================
fig, ax = plt.subplots(figsize=(12, 7))

colores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

# Simulación - TODOS los 5 nodos (para contexto)
for i in range(5):
    ax.plot(tiempos, V_hist[:, i], color=colores[i], 
            label=f'Nodo {i+1} (sim)', linewidth=2, linestyle='-', alpha=0.7)

# Datos experimentales - SOLO NODOS 1-4
ax.scatter(tiempos_exp, V1_exp, color=colores[0], s=10, label='Nodo 1 (exp)', alpha=0.8)
ax.scatter(tiempos_exp, V2_exp, color=colores[1], s=10, label='Nodo 2 (exp)', alpha=0.8)
ax.scatter(tiempos_exp, V3_exp, color=colores[2], s=10, label='Nodo 3 (exp)', alpha=0.8)
ax.scatter(tiempos_exp, V4_exp, color=colores[3], s=10, label='Nodo 4 (exp)', alpha=0.8)

ax.axhline(y=2.5, color='black', linestyle=':', alpha=0.5, label='50% de 5V (2.5V)')

ax.set_xlabel('Tiempo (s)', fontsize=14)
ax.set_ylabel('Voltaje (V)', fontsize=14)
ax.set_title('Comparación: Simulación vs. Experimento\nR = 33 kΩ, C = 100 µF, τ = 3.3 s', fontsize=16)
ax.legend(loc='upper left', fontsize=10, ncol=2)
ax.grid(True, linestyle='--', alpha=0.6)
ax.set_xlim(0, 60)
ax.set_ylim(0, 5.5)

plt.tight_layout()
plt.savefig('comparacion_teoria_experimento_33k_100uF.png', dpi=300, bbox_inches='tight')
plt.show()

# ============================================================
# 8. IMPRESIÓN DE RESULTADOS (SOLO NODOS 1-4)
# ============================================================
print("=" * 60)
print("RESULTADOS - RED RC 1×5 (R = 33 kΩ, C = 100 µF)")
print("=" * 60)
print(f"τ = R*C = {tau:.2f} s")
print(f"Voltaje de frontera: {V_frontera:.1f} V")
print("-" * 60)
print("Tiempos de subida al 50% (t_50):")
print("-" * 60)
print("  Nodo | Simulado (s) | Medido (s) | Diferencia")
print("-" * 60)

t50_exp_estimados = [5.5, 26.0, 42.0, np.nan]  # Nodos 1-4

for i in range(4):
    sim = f"{t50_sim[i]:.2f}" if not np.isnan(t50_sim[i]) else "---"
    exp = f"{t50_exp_estimados[i]:.1f}" if not np.isnan(t50_exp_estimados[i]) else "---"
    if i < 3:
        diff = f"{t50_exp_estimados[i] - t50_sim[i]:.1f}"
    else:
        diff = "---"
    print(f"  {i+1}    | {sim:>11} | {exp:>9} | {diff:>9}")
print("=" * 60)

V1_final_sim = V_hist[-1, 0]
print(f"\nVoltaje final simulado en Nodo 1: {V1_final_sim:.3f} V")
print(f"Voltaje final medido en Nodo 1: 3.372 V")

h = 0.01
alpha_sim = h**2 / tau
print(f"\nDifusividad equivalente: α = h²/τ = {alpha_sim:.3e} m²/s")
print("=" * 60)