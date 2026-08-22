# ============================================================
# ADQUISICIÓN DE DATOS CON ARDUINO - MODO MANUAL
# ============================================================
# Autor: Fernando Mellado C.
# Descripción: Lee datos del Arduino, espera señal de inicio,
# adquiere durante 60 segundos, luego espera confirmación
# manual de descarga para la siguiente repetición.
# ============================================================

import serial
import numpy as np
import pandas as pd
from datetime import datetime
import time

# ============================================================
# CONFIGURACIÓN
# ============================================================
PUERTO = 'COM8'                    # Cambiar según tu puerto
BAUDRATE = 115200
N_REPETICIONES = 5                 # Número de mediciones
DURACION_SEGUNDOS = 60             # Segundos por medición (debe coincidir con Arduino)

NOMBRE_BASE = f'datos_rc_{datetime.now().strftime("%Y%m%d_%H%M")}'

# ============================================================
# FUNCIÓN PARA ADQUIRIR DURANTE UN TIEMPO FIJO
# ============================================================
def adquirir_medicion(ser, duracion):
    """
    Lee datos del puerto serial durante 'duracion' segundos.
    Retorna: lista de tiempos (s) y voltajes (V) para cada canal.
    """
    tiempos = []
    V1, V2, V3, V4 = [], [], [], []
    
    inicio = time.time()
    while time.time() - inicio < duracion:
        if ser.in_waiting > 0:
            linea = ser.readline().decode('utf-8', errors='ignore').strip()
            if not linea:
                continue
            
            # Ignorar mensajes de control
            if linea.startswith('INICIO') or linea.startswith('FIN') or linea.startswith('==='):
                print(linea)
                continue
            
            # Ignorar cabeceras
            if linea.startswith('tiempo_ms') or linea.startswith('=== SISTEMA'):
                continue
            
            try:
                datos = linea.split(',')
                if len(datos) >= 5:  # tiempo, V1, V2, V3, V4
                    t = float(datos[0]) / 1000.0  # Convertir a segundos
                    tiempos.append(t)
                    V1.append(float(datos[1]))
                    V2.append(float(datos[2]))
                    V3.append(float(datos[3]))
                    V4.append(float(datos[4]))
            except ValueError:
                pass
    
    return np.array(tiempos), np.array(V1), np.array(V2), np.array(V3), np.array(V4)

# ============================================================
# CONEXIÓN AL ARDUINO
# ============================================================
try:
    ser = serial.Serial(PUERTO, BAUDRATE, timeout=0.1)
    print(f"✅ Conectado a {ser.name}")
    time.sleep(2)
except serial.SerialException as e:
    print(f"❌ Error: {e}")
    exit()

# ============================================================
# BUCLE PRINCIPAL DE ADQUISICIÓN
# ============================================================
all_data = []

for i in range(N_REPETICIONES):
    print("\n" + "="*60)
    print(f"📊 MEDICIÓN {i+1}/{N_REPETICIONES}")
    print("="*60)
    print("Presiona el BOTÓN en el Arduino para INICIAR la medición.")
    print("Esperando señal de inicio...")
    
    # Esperar la señal de inicio del Arduino
    inicio_recibido = False
    while not inicio_recibido:
        if ser.in_waiting > 0:
            linea = ser.readline().decode('utf-8', errors='ignore').strip()
            if "INICIO_MEDICION" in linea:
                print("⚡ Medicion INICIADA")
                inicio_recibido = True
                break
        time.sleep(0.01)
    
    # Adquirir datos durante DURACION_SEGUNDOS
    tiempos, v1, v2, v3, v4 = adquirir_medicion(ser, DURACION_SEGUNDOS)
    
    print(f"✅ Medicion completada. Muestras: {len(tiempos)}")
    
    # Guardar datos individuales
    df = pd.DataFrame({
        'Tiempo (s)': tiempos,
        'Canal_1 (V)': v1,
        'Canal_2 (V)': v2,
        'Canal_3 (V)': v3,
        'Canal_4 (V)': v4
    })
    all_data.append(df)
    
    nombre_individual = f'{NOMBRE_BASE}_medicion_{i+1}.xlsx'
    df.to_excel(nombre_individual, index=False)
    print(f"📁 Datos guardados en {nombre_individual}")
    
    # Si no es la última medición, esperar confirmación de descarga
    if i < N_REPETICIONES - 1:
        print("\n🔴 DESCARGA MANUAL REQUERIDA")
        print("Desconecta los capacitores (corto circuito o resistencia) para descargarlos.")
        input("Presiona ENTER cuando los capacitores estén completamente descargados y listos para la siguiente medición...")
        print("✅ Confirmado. Presiona el BOTÓN para la siguiente medición.")

# ============================================================
# CERRAR CONEXIÓN
# ============================================================
ser.close()
print("\n✅ Conexión cerrada.")

# ============================================================
# PROCESAMIENTO ESTADÍSTICO
# ============================================================
print("\n" + "="*60)
print("📊 PROCESANDO ESTADÍSTICAS")
print("="*60)

# Definir una malla temporal común
t_malla = np.arange(0, DURACION_SEGUNDOS, 0.05)

# Interpolar todas las mediciones a la malla común
V1_interp = []
V2_interp = []
V3_interp = []
V4_interp = []

for df in all_data:
    t = df['Tiempo (s)'].values
    v1 = df['Canal_1 (V)'].values
    v2 = df['Canal_2 (V)'].values
    v3 = df['Canal_3 (V)'].values
    v4 = df['Canal_4 (V)'].values
    
    # Interpolar (si hay datos)
    if len(t) > 1:
        V1_interp.append(np.interp(t_malla, t, v1))
        V2_interp.append(np.interp(t_malla, t, v2))
        V3_interp.append(np.interp(t_malla, t, v3))
        V4_interp.append(np.interp(t_malla, t, v4))
    else:
        # Si no hay datos, llenar con NaN
        V1_interp.append(np.full_like(t_malla, np.nan))
        V2_interp.append(np.full_like(t_malla, np.nan))
        V3_interp.append(np.full_like(t_malla, np.nan))
        V4_interp.append(np.full_like(t_malla, np.nan))

# Calcular medias y desviaciones estándar (ignorando NaN)
V1_mean = np.nanmean(V1_interp, axis=0)
V1_std = np.nanstd(V1_interp, axis=0)
V2_mean = np.nanmean(V2_interp, axis=0)
V2_std = np.nanstd(V2_interp, axis=0)
V3_mean = np.nanmean(V3_interp, axis=0)
V3_std = np.nanstd(V3_interp, axis=0)
V4_mean = np.nanmean(V4_interp, axis=0)
V4_std = np.nanstd(V4_interp, axis=0)

# Guardar resultados promediados
df_mean = pd.DataFrame({
    'Tiempo (s)': t_malla,
    'Canal_1_mean (V)': V1_mean,
    'Canal_1_std (V)': V1_std,
    'Canal_2_mean (V)': V2_mean,
    'Canal_2_std (V)': V2_std,
    'Canal_3_mean (V)': V3_mean,
    'Canal_3_std (V)': V3_std,
    'Canal_4_mean (V)': V4_mean,
    'Canal_4_std (V)': V4_std
})

nombre_promedio = f'{NOMBRE_BASE}_promedio.xlsx'
df_mean.to_excel(nombre_promedio, index=False)
print(f"📁 Datos promediados guardados en {nombre_promedio}")

# ============================================================
# IMPRIMIR RESUMEN ESTADÍSTICO
# ============================================================
print("\n" + "="*60)
print("📊 RESUMEN ESTADÍSTICO (t50 y voltajes finales)")
print("="*60)

for i, (mean, std) in enumerate(zip([V1_mean, V2_mean, V3_mean, V4_mean],
                                     [V1_std, V2_std, V3_std, V4_std])):
    # Tiempo de subida al 50% (2.5V)
    idx_t50 = np.where(mean >= 2.5)[0]
    if len(idx_t50) > 0:
        t50 = t_malla[idx_t50[0]]
        # Error en t50: estimado a partir de la desviación en ese punto
        t50_std = std[idx_t50[0]]
        print(f"Nodo {i+1}: t50 = {t50:.2f} ± {t50_std:.3f} s")
    else:
        print(f"Nodo {i+1}: No alcanza 2.5V en {DURACION_SEGUNDOS} s")

# Voltajes finales (al final de la malla)
idx_final = -1
print("\nVoltajes finales (t ≈ {:.1f} s):".format(t_malla[-1]))
for i, (mean, std) in enumerate(zip([V1_mean, V2_mean, V3_mean, V4_mean],
                                     [V1_std, V2_std, V3_std, V4_std])):
    print(f"  Nodo {i+1}: {mean[idx_final]:.3f} ± {std[idx_final]:.3f} V")

print("="*60)
print("✅ Procesamiento completado!")
