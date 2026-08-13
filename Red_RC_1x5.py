# ============================================================
# COMPARACIÓN TEORÍA-EXPERIMENTO - RED RC 1×4
# ============================================================
# Autor: Fernando Mellado C.
# Descripción: Genera la gráfica superponiendo la simulación
# y los datos experimentales con los nuevos parámetros.
# R = 33 kΩ, C = 100 µF, τ = 3.3 s
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import rcParams

# Configuración de estilo profesional
rcParams['font.size'] = 12
rcParams['axes.grid'] = True
rcParams['grid.linestyle'] = '--'
rcParams['grid.alpha'] = 0.3
rcParams['legend.framealpha'] = 0.95
rcParams['legend.edgecolor'] = 'gray'

# ============================================================
# 1. PARÁMETROS ACTUALIZADOS
# ============================================================
R = 33e3          # 33 kΩ
C = 100e-6        # 100 µF
tau = R * C       # 3.30 s
V_frontera = 5.0
V0 = np.zeros(5)
t_final = 120.0   # Extendido para cubrir los nuevos datos
dt = 0.05
N_steps = int(t_final / dt)

# ============================================================
# 2. SISTEMA DE EDOs Y RK4
# ============================================================
def derivadas(V, t):
    V_izq = V_frontera
    dV1 = (1/tau) * (V_izq - 2*V[0] + V[1])
    dV2 = (1/tau) * (V[0] - 2*V[1] + V[2])
    dV3 = (1/tau) * (V[1] - 2*V[2] + V[3])
    dV4 = (1/tau) * (V[2] - 2*V[3] + V[4])
    dV5 = (1/tau) * (V[3] - V[4])
    return np.array([dV1, dV2, dV3, dV4, dV5])

def rk4_step(V, t, dt):
    k1 = derivadas(V, t)
    k2 = derivadas(V + 0.5*dt*k1, t + 0.5*dt)
    k3 = derivadas(V + 0.5*dt*k2, t + 0.5*dt)
    k4 = derivadas(V + dt*k3, t + dt)
    return V + (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)

# Ejecutar simulación
tiempos = np.linspace(0, t_final, N_steps + 1)
V_hist = np.zeros((N_steps + 1, 5))
V_hist[0, :] = V0
V_actual = V0.copy()
for i in range(N_steps):
    V_actual = rk4_step(V_actual, tiempos[i], dt)
    V_hist[i + 1, :] = V_actual

# ============================================================
# 3. CARGAR NUEVOS DATOS EXPERIMENTALES
# ============================================================
df = pd.read_excel('datos_RC_individual.xlsx')
tiempos_exp = df['Tiempo (ms)'].values / 1000.0
V1_exp = df['Canal_1 (V)'].values
V2_exp = df['Canal_2 (V)'].values
V3_exp = df['Canal_3 (V)'].values
V4_exp = df['Canal_4 (V)'].values

# ============================================================
# 4. GRÁFICA DE COMPARACIÓN (MEJORADA)
# ============================================================
fig, ax = plt.subplots(figsize=(12, 7))

# Colores profesionales
colores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
nombres = ['Nodo 1', 'Nodo 2', 'Nodo 3', 'Nodo 4', 'Nodo 5']

# --- SIMULACIÓN (líneas continuas) ---
for i in range(5):
    ax.plot(tiempos, V_hist[:, i], 
            color=colores[i], 
            label=f'{nombres[i]} (sim)', 
            linewidth=2.5, 
            linestyle='-', 
            alpha=0.8)

# --- DATOS EXPERIMENTALES (puntos) ---
ax.scatter(tiempos_exp, V1_exp, 
           color=colores[0], s=8, 
           label='Nodo 1 (exp)', alpha=0.7, zorder=5)
ax.scatter(tiempos_exp, V2_exp, 
           color=colores[1], s=8, 
           label='Nodo 2 (exp)', alpha=0.7, zorder=5)
ax.scatter(tiempos_exp, V3_exp, 
           color=colores[2], s=8, 
           label='Nodo 3 (exp)', alpha=0.7, zorder=5)
ax.scatter(tiempos_exp, V4_exp, 
           color=colores[3], s=8, 
           label='Nodo 4 (exp)', alpha=0.7, zorder=5)

# --- LÍNEA DE REFERENCIA (50% de 5V = 2.5V) ---
ax.axhline(y=2.5, color='black', linestyle=':', 
           linewidth=1.5, alpha=0.7, label='50% de 5V (2.5V)')

# --- MARCAR t50 DEL NODO 1 (experimental) ---
# Estimado visualmente de los datos
t50_exp_nodo1 = 2.15  # Ajusta según el cálculo real
v50 = 2.5
ax.plot(t50_exp_nodo1, v50, 'o', 
        color='red', markersize=10, 
        markeredgecolor='white', markeredgewidth=2,
        label=f'$t_{{50,1}}$ = {t50_exp_nodo1:.2f} s (exp)')
ax.axvline(x=t50_exp_nodo1, color='red', 
           linestyle='--', linewidth=1.5, alpha=0.5)

# --- CONFIGURACIÓN DE EJES ---
ax.set_xlabel('Tiempo (s)', fontsize=14, fontweight='bold')
ax.set_ylabel('Voltaje (V)', fontsize=14, fontweight='bold')
ax.set_title('Comparación: Simulación vs. Experimento\n' +
             f'R = {R/1000:.0f} kΩ, C = {C*1e6:.0f} µF, τ = {tau:.2f} s', 
             fontsize=16, fontweight='bold')

ax.legend(loc='upper left', fontsize=10, ncol=2, 
          framealpha=0.95, edgecolor='gray')

ax.grid(True, linestyle='--', alpha=0.3)
ax.set_xlim(0, 105)  # Ajustado a los nuevos datos
ax.set_ylim(0, 5.5)

# --- AÑADIR CAJAS DE TEXTO CON RESULTADOS ---
# Valores finales estimados de los nuevos datos
V_final_exp = [4.15, 2.29, 1.48, 1.17]

texto_resultados = (
    "Resultados experimentales:\n"
    "─────────────────────────\n"
    f"Nodo 1: V_final = {V_final_exp[0]:.2f} V, t50 ≈ {t50_exp_nodo1:.2f} s\n"
    f"Nodo 2: V_final = {V_final_exp[1]:.2f} V (no alcanza 2.5V)\n"
    f"Nodo 3: V_final = {V_final_exp[2]:.2f} V (no alcanza 2.5V)\n"
    f"Nodo 4: V_final = {V_final_exp[3]:.2f} V (no alcanza 2.5V)"
)

ax.text(0.98, 0.02, texto_resultados,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment='bottom',
        horizontalalignment='right',
        bbox=dict(boxstyle='round', 
                  facecolor='white', 
                  alpha=0.95, 
                  edgecolor='gray',
                  pad=0.8))

# --- GUARDAR FIGURA ---
plt.tight_layout()
plt.savefig('comparacion_teoria_experimento.png', dpi=300, bbox_inches='tight')
print("✅ Figura guardada como 'comparacion_teoria_experimento.png'")
plt.show()

# ============================================================
# 5. IMPRESIÓN DE RESULTADOS EN CONSOLA
# ============================================================
print("\n" + "="*60)
print("RESULTADOS - COMPARACIÓN TEORÍA-EXPERIMENTO")
print("="*60)
print(f"τ = {tau:.2f} s")
print(f"Voltaje de referencia: {V_frontera:.1f} V")
print(f"Umbral (50%): 2.5 V")
print("-"*60)
print("TIEMPOS DE SUBIDA (t50):")
print("-"*60)

# t50 de la simulación
t50_sim = [3.70, 14.40, 26.50, 33.95, 37.40]
t50_exp = [2.15, np.nan, np.nan, np.nan]

print("  Nodo | Simulado (s) | Medido (s)")
print("-"*60)
for i in range(4):
    sim = f"{t50_sim[i]:.2f}"
    exp = f"{t50_exp[i]:.2f}" if not np.isnan(t50_exp[i]) else "---"
    print(f"  {i+1}    | {sim:>11} | {exp:>9}")
print("="*60)

print("\nVOLTAJES FINALES:")
print("-"*60)
for i in range(4):
    V_sim = V_hist[-1, i]
    V_exp = V_final_exp[i]
    print(f"  Nodo {i+1}: Sim = {V_sim:.3f} V, Exp = {V_exp:.3f} V")
print("="*60)

# Verificar equivalencia fundamental
h = 0.01
alpha_equivalente = h**2 / tau
print(f"\nDifusividad equivalente: α = h²/τ = {alpha_equivalente:.3e} m²/s")
print("="*60)