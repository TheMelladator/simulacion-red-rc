# ============================================================
# SIMULACIÓN DE RED RC 1x5 CON NEUMANN EN EXTREMO DERECHO
# ============================================================
# Autor: Fernando Mellado C.
# Descripción: Implementación del método RK4 para resolver
# el sistema de EDOs acopladas de una red RC de 5 nodos.
# Condiciones de frontera:
#   - Nodo 1: Dirichlet (V = V_frontera)
#   - Nodo 5: Neumann (flujo nulo, circuito abierto)
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Configuración de estilo para gráficas
rcParams['font.size'] = 12
rcParams['axes.grid'] = True
rcParams['grid.linestyle'] = '--'
rcParams['grid.alpha'] = 0.7

# ============================================================
# 1. PARÁMETROS DEL SISTEMA
# ============================================================
R = 10e3          # Resistencia (Ω)
C = 10e-6         # Capacitancia (F)
tau = R * C       # Constante de tiempo (s) -> 0.1 s

V_frontera = 5.0  # Voltaje aplicado en el nodo 1 (V)
V0 = np.zeros(5)  # Condición inicial: todos los nodos a 0V
t_final = 1.0     # Tiempo total de simulación (s)
dt = 1e-4         # Paso de integración (s)

# Número de pasos
N_steps = int(t_final / dt)

# ============================================================
# 2. DEFINICIÓN DEL SISTEMA DE EDOs
# ============================================================
# Vector de estado: V = [V1, V2, V3, V4, V5]
# Fronteras:
#   - Nodo 1 (izquierda): Dirichlet -> V0 = V_frontera
#   - Nodo 5 (derecha): Neumann -> flujo nulo (circuito abierto)

def derivadas(V, t):
    """
    Calcula las derivadas dV/dt para el sistema 1x5.
    V: vector de voltajes [V1, V2, V3, V4, V5]
    t: tiempo (no se usa explícitamente, pero se mantiene por compatibilidad)
    """
    # Condición de frontera izquierda (Dirichlet)
    V_izq = V_frontera
    
    # Nodo 1 (conectado a V_izq y V2)
    dV1 = (1/tau) * (V_izq - 2*V[0] + V[1])
    
    # Nodos interiores (2, 3, 4)
    dV2 = (1/tau) * (V[0] - 2*V[1] + V[2])
    dV3 = (1/tau) * (V[1] - 2*V[2] + V[3])
    dV4 = (1/tau) * (V[2] - 2*V[3] + V[4])
    
    # Nodo 5 (extremo derecho, Neumann: solo conectado a V4)
    dV5 = (1/tau) * (V[3] - V[4])
    
    return np.array([dV1, dV2, dV3, dV4, dV5])

# ============================================================
# 3. MÉTODO RK4 (IMPLEMENTACIÓN MANUAL)
# ============================================================
def rk4_step(V, t, dt):
    """
    Un paso del método de Runge-Kutta de cuarto orden.
    """
    k1 = derivadas(V, t)
    k2 = derivadas(V + 0.5*dt*k1, t + 0.5*dt)
    k3 = derivadas(V + 0.5*dt*k2, t + 0.5*dt)
    k4 = derivadas(V + dt*k3, t + dt)
    
    V_new = V + (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)
    return V_new

# ============================================================
# 4. EJECUTAR LA SIMULACIÓN
# ============================================================
# Inicializar arreglos para almacenar resultados
tiempos = np.linspace(0, t_final, N_steps + 1)
V_hist = np.zeros((N_steps + 1, 5))
V_hist[0, :] = V0

# Bucle principal de integración
V_actual = V0.copy()
for i in range(N_steps):
    V_actual = rk4_step(V_actual, tiempos[i], dt)
    V_hist[i + 1, :] = V_actual

# ============================================================
# 5. CÁLCULO DE TIEMPOS DE SUBIDA (t_50)
# ============================================================
def tiempo_subida_50(serie, V_final, tiempo):
    """
    Calcula el tiempo en que la señal alcanza el 50% del valor final.
    """
    umbral = 0.5 * V_final
    idx = np.where(serie >= umbral)[0]
    if len(idx) > 0:
        return tiempo[idx[0]]
    else:
        return np.nan

V_final_esperado = V_frontera
t50 = []
for i in range(5):
    t = tiempo_subida_50(V_hist[:, i], V_final_esperado, tiempos)
    t50.append(t)

# ============================================================
# 6. GENERACIÓN DE GRÁFICAS
# ============================================================
# Figura 1: Evolución temporal de los 5 nodos
fig1, ax1 = plt.subplots(figsize=(10, 6))

colores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
etiquetas = ['Nodo 1', 'Nodo 2', 'Nodo 3', 'Nodo 4', 'Nodo 5']

for i in range(5):
    ax1.plot(tiempos, V_hist[:, i], color=colores[i], 
             label=etiquetas[i], linewidth=2)

ax1.set_xlabel('Tiempo (s)', fontsize=14)
ax1.set_ylabel('Voltaje (V)', fontsize=14)
ax1.set_title('Evolución temporal de los voltajes en la red RC 1×5\n(Dirichlet izquierda, Neumann derecha)', fontsize=16)
ax1.legend(loc='upper left', fontsize=12)
ax1.grid(True, linestyle='--', alpha=0.6)

# Anotar los tiempos de subida al 50%
for i in range(5):
    if not np.isnan(t50[i]):
        ax1.axvline(x=t50[i], color=colores[i], linestyle=':', alpha=0.5)
        ax1.text(t50[i] + 0.02, V_final_esperado * 0.55, 
                 f'$t_{{50,{i+1}}}$', fontsize=10, color=colores[i])

ax1.set_xlim(0, 1.0)
ax1.set_ylim(0, 6.0)

plt.tight_layout()
plt.savefig('simulacion_red_1x5_neumann.png', dpi=300, bbox_inches='tight')
plt.show()

# ============================================================
# 7. IMPRESIÓN DE RESULTADOS
# ============================================================
print("=" * 60)
print("RESULTADOS DE LA SIMULACIÓN - RED RC 1×5")
print("(Dirichlet izquierda, Neumann derecha)")
print("=" * 60)
print(f"Parámetros: R = {R/1000:.1f} kΩ, C = {C*1e6:.1f} µF, τ = {tau:.3f} s")
print(f"Voltaje de frontera: {V_frontera:.1f} V")
print("-" * 60)
print("Tiempos de subida al 50% (t_50):")
print("-" * 60)
for i in range(5):
    if not np.isnan(t50[i]):
        print(f"  Nodo {i+1}: {t50[i]:.4f} s")
    else:
        print(f"  Nodo {i+1}: No alcanzó el 50%")
print("=" * 60)

# ============================================================
# 8. VERIFICACIÓN DE LA EQUIVALENCIA
# ============================================================
h = 0.01  # m (espaciado de la malla)
alpha_equivalente = h**2 / tau

print("\n" + "=" * 60)
print("VERIFICACIÓN DE LA EQUIVALENCIA FUNDAMENTAL")
print("=" * 60)
print(f"Espaciado de la malla: h = {h*100:.1f} cm = {h:.3f} m")
print(f"Constante de tiempo: τ = RC = {tau:.3f} s")
print(f"Difusividad equivalente: α = h²/τ = {alpha_equivalente:.2e} m²/s")
print("=" * 60)

# ============================================================
# 9. EXPORTAR DATOS
# ============================================================
datos = np.column_stack([tiempos, V_hist])
np.savetxt('simulacion_red_1x5_neumann.csv', datos, 
           delimiter=',', 
           header='t,V1,V2,V3,V4,V5', 
           comments='')
print("\nDatos guardados en 'simulacion_red_1x5_neumann.csv'")