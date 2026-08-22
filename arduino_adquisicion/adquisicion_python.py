import serial
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================
# CONFIGURACIÓN
# ============================================
PUERTO = 'COM8'
BAUDRATE = 115200
SUBMUESTREO = 5  # Tomar 1 de cada 5 puntos

# Configurar matplotlib
import matplotlib
matplotlib.use('TkAgg')

# ============================================
# FUNCIÓN DE AJUSTE EXPONENCIAL (MEJORADA)
# ============================================
def curva_carga(t, tau, Vmax, offset=0):
    return Vmax * (1 - np.exp(-t / tau)) + offset

def ajustar_curva_individual(tiempos, voltajes, label):
    """
    Ajuste individual por canal - NO FORZA Vmax
    """
    tiempos = np.array(tiempos)
    voltajes = np.array(voltajes)
    
    # Eliminar valores no finitos
    mask = np.isfinite(tiempos) & np.isfinite(voltajes)
    t_filt = tiempos[mask]
    v_filt = voltajes[mask]
    
    if len(t_filt) < 10:
        print(f"⚠️ {label}: Datos insuficientes")
        return None, None, None, None, None
    
    # Estimación inicial REALISTA basada en los datos
    v_max_est = np.max(v_filt)
    v_min_est = np.min(v_filt)
    
    # Estimar tau: buscar cuándo alcanza el 63.2% del voltaje máximo
    target = v_min_est + (v_max_est - v_min_est) * 0.632
    indices = np.where(v_filt >= target)[0]
    
    if len(indices) > 0:
        tau_est = t_filt[indices[0]]
    else:
        # Si nunca alcanza el 63.2%, usar el tiempo total como estimación
        tau_est = t_filt[-1] * 0.8
    
    # Limitar tau_est a un rango razonable
    tau_est = max(0.5, min(tau_est, 20))
    
    try:
        # Ajuste SIN FORZAR Vmax (dejamos que el algoritmo encuentre el valor)
        params, cov = curve_fit(curva_carga, t_filt, v_filt, 
                               p0=[tau_est, v_max_est, v_min_est],
                               bounds=([0.1, 0.01, -0.5], [20, v_max_est*1.5, 0.5]),
                               maxfev=10000)
        tau, Vmax, offset = params
        perr = np.sqrt(np.diag(cov)) if cov is not None else [0, 0, 0]
        return tau, Vmax, offset, perr[0], perr[1]
    except Exception as e:
        print(f"⚠️ Error en ajuste de {label}: {e}")
        # Fallback: usar estimación manual
        return tau_est, v_max_est, v_min_est, 0, 0

# ============================================
# CONEXIÓN AL ARDUINO
# ============================================
def conectar_arduino():
    print(f"🔌 Conectando a {PUERTO}...")
    try:
        ser = serial.Serial(PUERTO, BAUDRATE, timeout=0.1)
        ser.flushInput()
        print(f"✅ Conectado a {PUERTO}")
        return ser
    except serial.SerialException as e:
        print(f"❌ Error: {e}")
        exit()

# ============================================
# BASE DE DATOS
# ============================================
def inicializar_bd():
    conn = sqlite3.connect('mediciones_rc.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mediciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        tiempo_ms REAL,
        canal_1 REAL,
        canal_2 REAL,
        canal_3 REAL,
        canal_4 REAL,
        led_estado INTEGER,
        sesion_id INTEGER
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sesiones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        descripcion TEXT,
        r_kohm REAL,
        c_uf REAL,
        tau_teorica REAL,
        voltaje_maximo REAL
    )
    ''')
    
    return conn, cursor

# ============================================
# CAPTURA DE DATOS
# ============================================
def capturar_datos(ser, conn, cursor):
    print("\n🎯 Presiona el botón para INICIAR/DETENER")
    print("Presiona Ctrl+C para salir\n")
    
    sesion_id = None
    tiempos = []
    canal1, canal2, canal3, canal4 = [], [], [], []
    led_estados = []
    en_medicion = False
    
    try:
        while True:
            if ser.in_waiting > 0:
                linea = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if not linea:
                    continue
                
                print(linea)
                
                if linea == "INICIO_MEDICION":
                    print("\n⚡ INICIO DE MEDICIÓN")
                    en_medicion = True
                    
                    cursor.execute('''
                    INSERT INTO sesiones (descripcion, r_kohm, c_uf, tau_teorica, voltaje_maximo)
                    VALUES (?, ?, ?, ?, ?)
                    ''', ('Medición - ' + datetime.now().strftime('%H:%M:%S'), 33, 100, 3.3, 5.0))
                    sesion_id = cursor.lastrowid
                    conn.commit()
                    print(f"📊 Sesión ID: {sesion_id}")
                    
                    tiempos = []
                    canal1, canal2, canal3, canal4 = [], [], [], []
                    led_estados = []
                    continue
                
                if linea == "FIN_MEDICION" or linea == "=== MEDICIÓN DETENIDA ===":
                    print(f"\n🛑 FIN DE MEDICIÓN - Muestras: {len(tiempos)}")
                    en_medicion = False
                    break
                
                if linea.startswith('tiempo_ms') or linea.startswith('=== SISTEMA'):
                    continue
                
                if en_medicion and sesion_id is not None:
                    try:
                        datos = linea.split(',')
                        if len(datos) == 6:
                            t = float(datos[0])
                            v1 = float(datos[1])
                            v2 = float(datos[2])
                            v3 = float(datos[3])
                            v4 = float(datos[4])
                            led = int(datos[5])
                            
                            tiempos.append(t)
                            canal1.append(v1)
                            canal2.append(v2)
                            canal3.append(v3)
                            canal4.append(v4)
                            led_estados.append(led)
                            
                            if len(tiempos) % 20 == 0:
                                cursor.execute('''
                                INSERT INTO mediciones 
                                (tiempo_ms, canal_1, canal_2, canal_3, canal_4, led_estado, sesion_id)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                ''', (t, v1, v2, v3, v4, led, sesion_id))
                                conn.commit()
                    except:
                        pass
    
    except KeyboardInterrupt:
        print("\n\n⏹️ Programa interrumpido")
    
    return tiempos, canal1, canal2, canal3, canal4, led_estados, sesion_id

# ============================================
# GRÁFICA CON AJUSTE INDIVIDUAL
# ============================================
def graficar_resultados(tiempos, canal1, canal2, canal3, canal4, led_estados):
    """Gráfica con ajuste individual por canal"""
    
    # Submuestreo
    indices = slice(None, None, SUBMUESTREO)
    
    tiempos_s = np.array(tiempos[indices]) / 1000.0
    
    canales = {
        'C1': np.array(canal1[indices]),
        'C2': np.array(canal2[indices]),
        'C3': np.array(canal3[indices]),
        'C4': np.array(canal4[indices])
    }
    
    # Colores profesionales
    colores = {
        'C1': {'color': '#DC143C', 'marker': 'o', 'label': 'Canal 1'},
        'C2': {'color': '#1E90FF', 'marker': 's', 'label': 'Canal 2'},
        'C3': {'color': '#2E8B57', 'marker': '^', 'label': 'Canal 3'},
        'C4': {'color': '#FF8C00', 'marker': 'D', 'label': 'Canal 4'}
    }
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(14, 8))
    
    resultados = {}
    
    # Graficar cada canal con su propio ajuste
    for nombre, voltajes in canales.items():
        if len(voltajes) > 10:
            # Ajuste INDIVIDUAL (sin forzar Vmax)
            tau, Vmax, offset, err_tau, err_Vmax = ajustar_curva_individual(tiempos_s, voltajes, nombre)
            
            if tau is not None:
                resultados[nombre] = {
                    'tau': tau,
                    'Vmax': Vmax,
                    'offset': offset,
                    'error_tau': err_tau,
                    'error_Vmax': err_Vmax
                }
                
                # Datos experimentales
                ax.scatter(tiempos_s, voltajes, 
                          s=30,
                          alpha=0.4,
                          color=colores[nombre]['color'],
                          marker=colores[nombre]['marker'],
                          edgecolors='white',
                          linewidth=0.5,
                          label=f"{colores[nombre]['label']} (datos)",
                          zorder=3)
                
                # Curva ajustada (con el Vmax REAL de ese canal)
                t_teorico = np.linspace(0, max(tiempos_s), 500)
                v_teorico = curva_carga(t_teorico, tau, Vmax, offset)
                ax.plot(t_teorico, v_teorico, 
                       '-', 
                       color=colores[nombre]['color'], 
                       linewidth=2,
                       alpha=0.7,
                       label=f"{colores[nombre]['label']} τ={tau:.2f}s, Vmax={Vmax:.2f}V",
                       zorder=2)
                
                # ============================================
                # MARCADO DE τ/2 (INDIVIDUAL)
                # ============================================
                t_mitad = tau / 2
                v_mitad = curva_carga(t_mitad, tau, Vmax, offset)
                
                if t_mitad <= max(tiempos_s) * 1.1:
                    # Líneas de referencia
                    ax.hlines(y=v_mitad, xmin=0, xmax=t_mitad, 
                             colors=colores[nombre]['color'],
                             linestyles='--', linewidth=1.2, alpha=0.6)
                    ax.vlines(x=t_mitad, ymin=0, ymax=v_mitad, 
                             colors=colores[nombre]['color'],
                             linestyles='--', linewidth=1.2, alpha=0.6)
                    
                    # Punto
                    ax.plot(t_mitad, v_mitad, 'o', 
                           color=colores[nombre]['color'],
                           markersize=8,
                           markeredgecolor='white',
                           markeredgewidth=1.5,
                           zorder=4)
                    
                    # Etiqueta
                    ax.text(t_mitad * 1.02, v_mitad * 1.05, 
                           f'τ/2={t_mitad:.2f}s',
                           fontsize=8,
                           color=colores[nombre]['color'],
                           bbox=dict(boxstyle='round,pad=0.2', 
                                    facecolor='white', 
                                    alpha=0.7,
                                    edgecolor=colores[nombre]['color']))
    
    # ============================================
    # CONFIGURACIÓN DE LA GRÁFICA
    # ============================================
    ax.set_xlabel('Tiempo (s)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Voltaje (V)', fontsize=13, fontweight='bold')
    ax.set_title('Carga de 4 Capacitores en Malla RC\nCada canal con su propia constante de tiempo', 
                 fontsize=15, fontweight='bold')
    ax.grid(True, alpha=0.2, linestyle='--')
    
    # Límites
    ax.set_xlim(0, max(tiempos_s) * 1.05)
    max_voltaje = max([max(v) for v in canales.values() if len(v) > 0])
    ax.set_ylim(-0.1, max_voltaje * 1.15)
    
    # ============================================
    # LEYENDA MEJORADA
    # ============================================
    handles, labels = ax.get_legend_handles_labels()
    
    handles_datos = []
    labels_datos = []
    handles_ajuste = []
    labels_ajuste = []
    
    for h, l in zip(handles, labels):
        if '(datos)' in l:
            handles_datos.append(h)
            labels_datos.append(l)
        elif 'τ=' in l:
            handles_ajuste.append(h)
            labels_ajuste.append(l)
    
    if handles_datos:
        leg1 = ax.legend(handles_datos, labels_datos, 
                        loc='upper left', 
                        bbox_to_anchor=(0.02, 0.98),
                        framealpha=0.95,
                        edgecolor='gray',
                        fontsize=10,
                        ncol=2)
        ax.add_artist(leg1)
    
    if handles_ajuste:
        leg2 = ax.legend(handles_ajuste, labels_ajuste, 
                        loc='lower left',
                        bbox_to_anchor=(0.02, 0.02),
                        framealpha=0.95,
                        edgecolor='gray',
                        fontsize=9,
                        ncol=2)
        ax.add_artist(leg2)
    
    # ============================================
    # TABLA DE RESULTADOS
    # ============================================
    if resultados:
        texto_tabla = "Resultados del ajuste (individual):\n"
        texto_tabla += "-" * 40 + "\n"
        for nombre, datos in resultados.items():
            texto_tabla += f"{nombre}: τ={datos['tau']:.3f}s, Vmax={datos['Vmax']:.3f}V\n"
        
        ax.text(0.98, 0.98, texto_tabla,
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment='top',
                horizontalalignment='right',
                bbox=dict(boxstyle='round', 
                         facecolor='white', 
                         alpha=0.9, 
                         edgecolor='gray',
                         pad=0.5))
    
    plt.tight_layout()
    plt.savefig('grafica_RC_individual.png', dpi=300, bbox_inches='tight')
    print("\n📊 Gráfica guardada como 'grafica_RC_individual.png'")
    
    try:
        plt.show()
    except:
        print("   Puedes abrir el archivo 'grafica_RC_individual.png' manualmente")
    
    return resultados

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================
def main():
    print("=" * 60)
    print("   SISTEMA RC - AJUSTE INDIVIDUAL POR CANAL")
    print("=" * 60)
    
    ser = conectar_arduino()
    conn, cursor = inicializar_bd()
    
    tiempos, canal1, canal2, canal3, canal4, led_estados, sesion_id = capturar_datos(ser, conn, cursor)
    
    ser.close()
    conn.close()
    
    if len(tiempos) == 0:
        print("\n❌ No se capturaron datos.")
        return
    
    max_voltaje = max([max(canal1) if canal1 else 0,
                       max(canal2) if canal2 else 0,
                       max(canal3) if canal3 else 0,
                       max(canal4) if canal4 else 0])
    
    print(f"\n✅ Datos capturados: {len(tiempos)} muestras")
    print(f"   Duración: {tiempos[-1] - tiempos[0]:.1f} ms")
    print(f"   Voltaje máximo total: {max_voltaje:.3f} V")
    
    resultados = graficar_resultados(tiempos, canal1, canal2, canal3, canal4, led_estados)
    
    # Guardar datos
    df = pd.DataFrame({
        'Tiempo (ms)': tiempos,
        'Canal_1 (V)': canal1,
        'Canal_2 (V)': canal2,
        'Canal_3 (V)': canal3,
        'Canal_4 (V)': canal4,
        'LED_ON': led_estados
    })
    
    try:
        df.to_excel('datos_RC_individual.xlsx', index=False)
        print("📁 Datos guardados en 'datos_RC_individual.xlsx'")
    except:
        df.to_csv('datos_RC_individual.csv', index=False)
        print("📁 Datos guardados en 'datos_RC_individual.csv'")
    
    print("\n" + "=" * 60)
    print("   RESULTADOS FINALES")
    print("=" * 60)
    if resultados:
        for nombre, datos in resultados.items():
            # Calcular error SOLO si tau es razonable (no forzado)
            if datos['tau'] < 10:
                error = abs(datos['tau'] - 3.3) / 3.3 * 100
                print(f"{nombre}: τ = {datos['tau']:.3f}s  |  Vmax = {datos['Vmax']:.3f}V  |  Error vs teórico: {error:.1f}%")
            else:
                print(f"{nombre}: τ = {datos['tau']:.3f}s  |  Vmax = {datos['Vmax']:.3f}V  |  ⚠️ No alcanza equilibrio en el tiempo medido")
    else:
        print("⚠️ No se pudieron ajustar las curvas")
    
    print("\n✅ Proceso completado!")

if __name__ == "__main__":
    main()
