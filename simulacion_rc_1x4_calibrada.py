# ============================================================
# SIMULACIÓN DE RED RC 1×4 - TOPOLOGÍA REAL CALIBRADA
# ============================================================
# Autor: Fernando Mellado C.
# Descripción: Simulación con valores medidos de componentes.
# 
# PARÁMETROS REALES:
#   R_fuente = 32.7 kΩ
#   R_int = 65.4 kΩ
#   C = 98.2 µF
#   V_fuente = 4.99 V
#   τ_fuente = 3.211 s
#   τ_int = 6.422 s
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.size'] = 12
rcParams['axes.grid'] = True
rcParams['grid.linestyle'] = '--'
rcParams['grid.alpha'] = 0.3

# ============================================================
# PARÁMETROS REALES
# ============================================================
R_fuente = 32.7e3      # 32.7 kΩ
R_int = 65.4e3         # 65.4 kΩ
C = 98.2e-6            # 98.2 µF

tau_fuente = R_fuente * C  # 3.211 s
tau_int = R_int * C        # 6.422 s

V_fuente = 4.99
V0 = np.zeros(4)
t_final = 120.0
dt = 0.05
N_steps = int(t_final / dt)

# ============================================================
# SISTEMA DE EDOs
# ============================================================
def derivadas(V, t):
    V1, V2, V3, V4 = V
    
    dV1 = (1/tau_fuente) * (V_fuente - V1) + (1/tau_int) * (V2 - V1)
    dV2 = (1/tau_int) * (V1 - 2*V2 + V3)
    dV3 = (1/tau_int) * (V2 - 2*V3 + V4)
    dV4 = (1/tau_int) * (V3 - V4)
    
    return np.array([dV1, dV2, dV3, dV4])

def rk4_step(V, t, dt):
    k1 = derivadas(V, t)
    k2 = derivadas(V + 0.5*dt*k1, t + 0.5*dt)
    k3 = derivadas(V + 0.5*dt*k2, t + 0.5*dt)
    k4 = derivadas(V + dt*k3, t + dt)
    return V + (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)

# Ejecutar
tiempos = np.linspace(0, t_final, N_steps + 1)
V_hist = np.zeros((N_steps + 1, 4))
V_hist[0, :] = V0

V_actual = V0.copy()
for i in range(N_steps):
    V_actual = rk4_step(V_actual, tiempos[i], dt)
    V_hist[i + 1, :] = V_actual

# ============================================================
# CÁLCULO DE t50
# ============================================================
def t50(serie):
    umbral = 2.5
    idx = np.where(serie >= umbral)[0]
    return tiempos[idx[0]] if len(idx) > 0 else np.nan

t50_sim = [t50(V_hist[:, i]) for i in range(4)]

# ============================================================
# IMPRESIÓN
# ============================================================
print("=" * 60)
print("SIMULACIÓN CALIBRADA - RED RC 1×4")
print("=" * 60)
print(f"R_fuente = {R_fuente/1000:.1f} kΩ")
print(f"R_int = {R_int/1000:.1f} kΩ")
print(f"C = {C*1e6:.1f} µF")
print(f"V_fuente = {V_fuente:.2f} V")
print(f"τ_fuente = {tau_fuente:.3f} s")
print(f"τ_int = {tau_int:.3f} s")
print("-" * 60)
print("Tiempos de subida al 50% (t50):")
for i in range(4):
    if not np.isnan(t50_sim[i]):
        print(f"  Nodo {i+1}: {t50_sim[i]:.2f} s")
    else:
        print(f"  Nodo {i+1}: No alcanzó el 50%")
print("-" * 60)
print("Voltajes finales (t = 120 s):")
for i in range(4):
    print(f"  Nodo {i+1}: {V_hist[-1, i]:.3f} V")
print("=" * 60)

# ============================================================
# GRÁFICA
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))

colores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
nombres = ['Nodo 1', 'Nodo 2', 'Nodo 3', 'Nodo 4']

for i in range(4):
    ax.plot(tiempos, V_hist[:, i], color=colores[i],
            label=f'{nombres[i]}', linewidth=2.5, alpha=0.8)

ax.axhline(y=2.5, color='black', linestyle=':', linewidth=1.5, alpha=0.7)

for i in range(4):
    if not np.isnan(t50_sim[i]):
        ax.axvline(x=t50_sim[i], color=colores[i], linestyle='--', linewidth=1.2, alpha=0.5)
        ax.text(t50_sim[i] + 0.5, 0.3 + i*0.5,
                f'$t_{{50,{i+1}}}$ = {t50_sim[i]:.2f}s',
                fontsize=9, color=colores[i])

ax.set_xlabel('Tiempo (s)', fontsize=14, fontweight='bold')
ax.set_ylabel('Voltaje (V)', fontsize=14, fontweight='bold')
ax.set_title('Simulación calibrada\n' +
             f'R_s = {R_fuente/1000:.1f} kΩ, R_d = {R_int/1000:.1f} kΩ, ' +
             f'C = {C*1e6:.1f} µF',
             fontsize=15, fontweight='bold')

ax.legend(loc='upper left', fontsize=11)
ax.grid(True, linestyle='--', alpha=0.3)
ax.set_xlim(0, 120)
ax.set_ylim(0, 5.5)

plt.tight_layout()
plt.savefig('simulacion_red_1x4_real.png', dpi=300, bbox_inches='tight')
plt.show()

# ============================================================
# VERIFICACIÓN DE LA EQUIVALENCIA FUNDAMENTAL
# ============================================================
h = 0.01
alpha = h**2 / tau_int
print(f"\nDifusividad equivalente: α = h²/τ_int = {alpha:.3e} m²/s")
print("=" * 60)
