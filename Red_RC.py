# ============================================================
# COMPARACIÓN TEORÍA-EXPERIMENTO - RED RC 1×4 (TOPOLOGÍA REAL)
# ============================================================
# Autor: Fernando Mellado C.
# Descripción: Genera la gráfica superponiendo la simulación
# con la topología real (R_fuente = 33k, R_int = 66k)
# y los datos experimentales sin carga.
# ============================================================
# PARÁMETROS REALES:
#   R_fuente = 33 kΩ  (resistencia de la fuente al Nodo 1)
#   R_int = 66 kΩ     (resistencia efectiva entre nodos, 2R)
#   C = 100 µF
#   τ_fuente = R_fuente * C = 3.30 s
#   τ_int = R_int * C = 6.60 s
#   α = h² / τ_int = 1.515 × 10⁻⁵ m²/s
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import rcParams
from scipy.interpolate import interp1d
from sklearn.metrics import mean_squared_error

# Configuración de estilo profesional
rcParams['font.size'] = 12
rcParams['axes.grid'] = True
rcParams['grid.linestyle'] = '--'
rcParams['grid.alpha'] = 0.3
rcParams['legend.framealpha'] = 0.95
rcParams['legend.edgecolor'] = 'gray'

# ============================================================
# 1. PARÁMETROS DE LA TOPOLOGÍA REAL (1×4)
# ============================================================
R_fuente = 33e3      # 33 kΩ (resistencia de la fuente)
R_int = 2 * R_fuente # 66 kΩ (resistencia efectiva entre nodos)
C = 100e-6           # 100 µF

tau_fuente = R_fuente * C  # 3.30 s
tau_int = R_int * C        # 6.60 s

V_fuente = 5.0
V0 = np.zeros(4)            # 4 nodos (N=4)
t_final = 120.0
dt = 0.05
N_steps = int(t_final / dt)

# ============================================================
# 2. SISTEMA DE EDOs (TOPOLOGÍA REAL 1×4)
# ============================================================
# Ecuaciones de nodo:
#   dV1/dt = (1/τ_fuente)*(V_fuente - V1) + (1/τ_int)*(V2 - V1)
#   dV2/dt = (1/τ_int)*(V1 - 2*V2 + V3)
#   dV3/dt = (1/τ_int)*(V2 - 2*V3 + V4)
#   dV4/dt = (1/τ_int)*(V3 - V4)   [Neumann en extremo derecho]

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
tiempos_sim = np.linspace(0, t_final, N_steps + 1)
V_hist = np.zeros((N_steps + 1, 4))
V_hist[0, :] = V0

V_actual = V0.copy()
for i in range(N_steps):
    V_actual = rk4_step(V_actual, tiempos_sim[i], dt)
    V_hist[i + 1, :] = V_actual

# ============================================================
# 4. CÁLCULO DE t50 (SIMULACIÓN)
# ============================================================
def t50(serie, tiempos):
    umbral = 2.5  # 50% de 5V
    idx = np.where(serie >= umbral)[0]
    return tiempos[idx[0]] if len(idx) > 0 else np.nan

t50_sim = [t50(V_hist[:, i], tiempos_sim) for i in range(4)]

print("="*60)
print("SIMULACIÓN CON TOPOLOGÍA REAL (1×4)")
print("="*60)
print(f"R_fuente = {R_fuente/1000:.0f} kΩ")
print(f"R_int = {R_int/1000:.0f} kΩ")
print(f"C = {C*1e6:.0f} µF")
print(f"τ_fuente = {tau_fuente:.2f} s")
print(f"τ_int = {tau_int:.2f} s")
print("-"*60)
print("t50 (simulación):")
for i in range(4):
    if not np.isnan(t50_sim[i]):
        print(f"  Nodo {i+1}: {t50_sim[i]:.2f} s")
    else:
        print(f"  Nodo {i+1}: No alcanzó el 50%")
print("="*60)

# ============================================================
# 5. CARGAR DATOS EXPERIMENTALES (SIN CARGA)
# ============================================================
df = pd.read_excel('datos_RC_individual.xlsx')
tiempos_exp = df['Tiempo (ms)'].values / 1000.0
V1_exp = df['Canal_1 (V)'].values
V2_exp = df['Canal_2 (V)'].values
V3_exp = df['Canal_3 (V)'].values
V4_exp = df['Canal_4 (V)'].values

V_exp = np.column_stack([V1_exp, V2_exp, V3_exp, V4_exp])

# ============================================================
# 6. CÁLCULO DE RMSE Y NRMSE
# ============================================================
rmse_values = []
nrmse_values = []

for i in range(4):
    # Interpolar simulación a tiempos experimentales
    f_interp = interp1d(tiempos_sim, V_hist[:, i], 
                        bounds_error=False, fill_value="extrapolate")
    V_sim_interp = f_interp(tiempos_exp)
    
    # Eliminar NaN si existen
    mask = ~np.isnan(V_sim_interp)
    rmse = np.sqrt(mean_squared_error(V_exp[mask, i], V_sim_interp[mask]))
    rmse_values.append(rmse)
    
    # NRMSE normalizado por V_ref = 5V
    nrmse = (rmse / V_fuente) * 100
    nrmse_values.append(nrmse)

print("\nMÉTRICAS DE CONCORDANCIA:")
print("-"*60)
print("Nodo | RMSE (V) | NRMSE (%)")
print("-"*60)
for i in range(4):
    print(f"  {i+1}  |  {rmse_values[i]:.4f}   |   {nrmse_values[i]:.2f}%")
print("="*60)

# ============================================================
# 7. CÁLCULO DE t50 EXPERIMENTAL
# ============================================================
t50_exp = [t50(V1_exp, tiempos_exp),
           t50(V2_exp, tiempos_exp),
           t50(V3_exp, tiempos_exp),
           t50(V4_exp, tiempos_exp)]

print("\nt50 experimental:")
for i in range(4):
    if not np.isnan(t50_exp[i]):
        print(f"  Nodo {i+1}: {t50_exp[i]:.2f} s")
    else:
        print(f"  Nodo {i+1}: No alcanzó el 50%")
print("="*60)

# ============================================================
# 8. GRÁFICA CON SUBPLOTS
# ============================================================
SUBMUESTREO = 10
idx_sub = slice(None, None, SUBMUESTREO)

tiempos_sub = tiempos_exp[idx_sub]
V1_sub = V1_exp[idx_sub]
V2_sub = V2_exp[idx_sub]
V3_sub = V3_exp[idx_sub]
V4_sub = V4_exp[idx_sub]
datos_exp_sub = [V1_sub, V2_sub, V3_sub, V4_sub]

fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.flatten()

colores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
nombres = ['Nodo 1', 'Nodo 2', 'Nodo 3', 'Nodo 4']

for i, ax in enumerate(axes):
    # Simulación (línea continua)
    ax.plot(tiempos_sim, V_hist[:, i], 
            color=colores[i], linewidth=2.5, 
            label='Simulación (topología real)', alpha=0.8)
    
    # Datos experimentales (puntos)
    ax.scatter(tiempos_sub, datos_exp_sub[i], 
               color=colores[i], s=10, alpha=0.6,
               label='Experimental', zorder=5)
    
    # Línea de referencia al 50%
    ax.axhline(y=2.5, color='black', linestyle=':', 
               linewidth=1.2, alpha=0.5, label='50% de 5V')
    
    # Marcar t50 si existe
    if not np.isnan(t50_sim[i]):
        ax.axvline(x=t50_sim[i], color=colores[i], 
                   linestyle='--', linewidth=1.0, alpha=0.4)
        ax.text(t50_sim[i] + 1, 0.3, f't50={t50_sim[i]:.1f}s', 
                fontsize=8, color=colores[i])
    
    ax.set_xlabel('Tiempo (s)', fontsize=12)
    ax.set_ylabel('Voltaje (V)', fontsize=12)
    ax.set_title(f'{nombres[i]}', fontsize=14, fontweight='bold')
    ax.legend(loc='lower right', fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 5.5)

plt.tight_layout()
plt.savefig('comparacion_subplots_topologia_real.png', dpi=300, bbox_inches='tight')
print("\n Figura guardada como 'comparacion_subplots_topologia_real.png'")
plt.show()

# ============================================================
# 9. VERIFICACIÓN DE LA EQUIVALENCIA FUNDAMENTAL
# ============================================================
h = 0.01  # 1 cm
alpha_equivalente = h**2 / tau_int

print("\n" + "="*60)
print("VERIFICACIÓN DE LA EQUIVALENCIA FUNDAMENTAL")
print("="*60)
print(f"Espaciado de malla: h = {h*100:.1f} cm = {h:.3f} m")
print(f"Constante de difusión: τ_int = R_int·C = {tau_int:.2f} s")
print(f"Difusividad equivalente: α = h²/τ_int = {alpha_equivalente:.3e} m²/s")
print("="*60)
