# ============================================================
# SIMULACIÓN DE RED RC 1×4 - TOPOLOGÍA REAL
# ============================================================
# Autor: Fernando Mellado C.
# Descripción: Simulación de la red RC 1×4 con la topología
# real: R_fuente = 33 kΩ, R_int = 66 kΩ (2R).
# Condiciones de frontera: Dirichlet izquierda (5V) y
# Neumann derecha (circuito abierto).
# ============================================================
# PARÁMETROS:
#   R_fuente = 33 kΩ
#   R_int = 66 kΩ
#   C = 100 µF
#   τ_fuente = R_fuente * C = 3.30 s
#   τ_int = R_int * C = 6.60 s
#   V_fuente = 5 V
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Configuración de estilo profesional
rcParams['font.size'] = 12
rcParams['axes.grid'] = True
rcParams['grid.linestyle'] = '--'
rcParams['grid.alpha'] = 0.3
rcParams['legend.framealpha'] = 0.95
rcParams['legend.edgecolor'] = 'gray'

# ============================================================
# 1. PARÁMETROS DE LA TOPOLOGÍA REAL
# ============================================================
R_fuente = 33e3      # 33 kΩ (resistencia de la fuente)
R_int = 66e3         # 66 kΩ (resistencia efectiva entre nodos, 2R)
C = 100e-6           # 100 µF

tau_fuente = R_fuente * C  # 3.30 s
tau_int = R_int * C        # 6.60 s

V_fuente = 5
V0 = np.zeros(4)            # 4 nodos
t_final = 120.0
dt = 0.05
N_steps = int(t_final / dt)

# ============================================================
# 2. SISTEMA DE EDOs (TOPOLOGÍA REAL 1×4)
# ============================================================
def derivadas(V, t):
    V1, V2, V3, V4 = V

    # Nodo 1: fuente (33k) + nodo 2 (66k)
    dV1 = (1/tau_fuente) * (V_fuente - V1) + (1/tau_int) * (V2 - V1)

    # Nodo 2: nodo 1 (66k) + nodo 3 (66k)
    dV2 = (1/tau_int) * (V1 - 2*V2 + V3)

    # Nodo 3: nodo 2 (66k) + nodo 4 (66k)
    dV3 = (1/tau_int) * (V2 - 2*V3 + V4)

    # Nodo 4: nodo 3 (66k) + Neumann (circuito abierto)
    dV4 = (1/tau_int) * (V3 - V4)

    return np.array([dV1, dV2, dV3, dV4])

def rk4_step(V, t, dt):
    k1 = derivadas(V, t)
    k2 = derivadas(V + 0.5*dt*k1, t + 0.5*dt)
    k3 = derivadas(V + 0.5*dt*k2, t + 0.5*dt)
    k4 = derivadas(V + dt*k3, t + dt)
    return V + (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)

# ============================================================
# 3. EJECUTAR SIMULACIÓN
# ============================================================
tiempos = np.linspace(0, t_final, N_steps + 1)
V_hist = np.zeros((N_steps + 1, 4))
V_hist[0, :] = V0

V_actual = V0.copy()
for i in range(N_steps):
    V_actual = rk4_step(V_actual, tiempos[i], dt)
    V_hist[i + 1, :] = V_actual

# ============================================================
# 4. CÁLCULO DE t50 (SIMULACIÓN)
# ============================================================
def t50(serie):
    umbral = 2.5  # 50% de 5V
    idx = np.where(serie >= umbral)[0]
    return tiempos[idx[0]] if len(idx) > 0 else np.nan

t50_sim = [t50(V_hist[:, i]) for i in range(4)]

# ============================================================
# 5. GRÁFICA DE SIMULACIÓN (4 NODOS JUNTOS)
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))

colores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
nombres = ['Nodo 1', 'Nodo 2', 'Nodo 3', 'Nodo 4']

# Graficar simulación
for i in range(4):
    ax.plot(tiempos, V_hist[:, i],
            color=colores[i],
            label=f'{nombres[i]}',
            linewidth=2.5,
            linestyle='-',
            alpha=0.8)

# Línea de referencia al 50% (2.5 V)
ax.axhline(y=2.5, color='black', linestyle=':',
           linewidth=1.5, alpha=0.7, label='50% de 5V (2.5V)')

# Marcar t50 para cada nodo
for i in range(4):
    if not np.isnan(t50_sim[i]):
        ax.axvline(x=t50_sim[i], color=colores[i],
                   linestyle='--', linewidth=1.2, alpha=0.6)
        ax.text(t50_sim[i] + 1, 0.3 + i*0.5,
                f'$t_{{50,{i+1}}}$ = {t50_sim[i]:.1f}s',
                fontsize=9, color=colores[i],
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

# Configuración
ax.set_xlabel('Tiempo (s)', fontsize=14, fontweight='bold')
ax.set_ylabel('Voltaje (V)', fontsize=14, fontweight='bold')
ax.set_title('Simulación de la red RC 1×4 (Topología real)\n' +
             f'$R_s = {R_fuente/1000:.0f}$ kΩ, $R_d = {R_int/1000:.0f}$ kΩ, ' +
             f'$C = {C*1e6:.0f}$ µF',
             fontsize=15, fontweight='bold')

ax.legend(loc='upper left', fontsize=11)
ax.grid(True, linestyle='--', alpha=0.3)
ax.set_xlim(0, 120)
ax.set_ylim(0, 5.5)

plt.tight_layout()
plt.savefig('figura4_simulacion_topologia_real.png', dpi=300, bbox_inches='tight')
plt.show()

# ============================================================
# 6. IMPRESIÓN DE RESULTADOS
# ============================================================
print("=" * 60)
print("SIMULACIÓN - RED RC 1×4 (TOPOLOGÍA REAL)")
print("=" * 60)
print(f"R_fuente = {R_fuente/1000:.3f} kΩ")
print(f"R_int = {R_int/1000:.3f} kΩ")
print(f"τ_fuente = {tau_fuente:.3f} s")
print(f"τ_int = {tau_int:.3f} s")
print(f"Voltaje de fuente: {V_fuente:.3f} V")
print("-" * 60)
print("Tiempos de subida al 50% (t50):")
print("-" * 60)
for i in range(4):
    if not np.isnan(t50_sim[i]):
        print(f"  Nodo {i+1}: {t50_sim[i]:.2f} s")
    else:
        print(f"  Nodo {i+1}: No alcanzó el 50% en {t_final:.3f} s")
print("-" * 60)
print("Voltajes finales (t = 120 s):")
for i in range(4):
    print(f"  Nodo {i+1}: {V_hist[-1, i]:.3f} V")
print("=" * 60)

# Verificar equivalencia fundamental
h = 0.01
alpha_equivalente = h**2 / tau_int
print(f"\nDifusividad equivalente: α = h²/τ_int = {alpha_equivalente:.3e} m²/s")
print("=" * 60)
