# ============================================================
# ADQUISICIÓN DE DATOS CON ARDUINO - 5 REPETICIONES
# ============================================================
# Autor: Fernando Mellado C.
# Descripción: Realiza 5 mediciones consecutivas con descarga
# entre ellas y calcula estadísticas.
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
N_REPETICIONES = 5
DURACION = 60
TIEMPO_DESCARGA = 120

NOMBRE_BASE = f'datos_rc_{datetime.now().strftime("%Y%m%d_%H%M")}'

# ============================================================
# FUNCIÓN PARA ADQUIRIR UNA MEDICIÓN
# ============================================================
def adquirir_medicion(ser, duracion):
    tiempos = []
    V1, V2, V3, V4 = [], [], [], []
    
    inicio = time.time()
    while time.time() - inicio < duracion:
        if ser.in_waiting > 0:
            linea = ser.readline().decode('utf-8', errors='ignore').strip()
            if not linea:
                continue
            if linea.startswith('INICIO') or linea.startswith('FIN') or linea.startswith('==='):
                print(linea)
                continue
            if linea.startswith('tiempo_ms') or linea.startswith('=== SISTEMA'):
                continue
            try:
                datos = linea.split(',')
                if len(datos) >= 5:
                    t = float(datos[0]) / 1000.0
                    tiempos.append(t)
                    V1.append(float(datos[1]))
                    V2.append(float(datos[2]))
                    V3.append(float(datos[3]))
                    V4.append(float(datos[4]))
            except ValueError:
                pass
    
    return np.array(tiempos), np.array(V1), np.array(V2), np.array(V3), np.array(V4)

# ============================================================
# CONEXIÓN
# ============================================================
try:
    ser = serial.Serial(PUERTO, BAUDRATE, timeout=0.1)
    print(f"✅ Conectado a {ser.name}")
    time.sleep(2)
except serial.SerialException as e:
    print(f"❌ Error: {e}")
    exit()

all_data = []

for i in range(N_REPETICIONES):
    print("\n" + "="*60)
    print(f"📊 MEDICIÓN {i+1}/{N_REPETICIONES}")
    print("="*60)
    print("Presiona el BOTÓN en el Arduino para INICIAR la medición.")
    print("Esperando señal de inicio...")
    
    inicio_recibido = False
    while not inicio_recibido:
        if ser.in_waiting > 0:
            linea = ser.readline().decode('utf-8', errors='ignore').strip()
            if "INICIO_MEDICION" in linea:
                print("⚡ Medicion INICIADA")
                inicio_recibido = True
                break
        time.sleep(0.01)
    
    tiempos, v1, v2, v3, v4 = adquirir_medicion(ser, DURACION)
    print(f"✅ Medicion completada. Muestras: {len(tiempos)}")
    
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
    
    if i < N_REPETICIONES - 1:
        print(f"\n⏳ Esperando {TIEMPO_DESCARGA} s para descarga de capacitores...")
        time.sleep(TIEMPO_DESCARGA)
        print("✅ Descarga completada. Presiona el BOTÓN para la siguiente medición.")

ser.close()
print("\n✅ Conexión cerrada.")

# ============================================================
# PROCESAMIENTO ESTADÍSTICO
# ============================================================
print("\n" + "="*60)
print("📊 PROCESANDO ESTADÍSTICAS")
print("="*60)

t_malla = np.arange(0, DURACION, 0.05)

V1_interp, V2_interp, V3_interp, V4_interp = [], [], [], []

for df in all_data:
    t = df['Tiempo (s)'].values
    v1 = df['Canal_1 (V)'].values
    v2 = df['Canal_2 (V)'].values
    v3 = df['Canal_3 (V)'].values
    v4 = df['Canal_4 (V)'].values
    
    if len(t) > 1:
        V1_interp.append(np.interp(t_malla, t, v1))
        V2_interp.append(np.interp(t_malla, t, v2))
        V3_interp.append(np.interp(t_malla, t, v3))
        V4_interp.append(np.interp(t_malla, t, v4))
    else:
        V1_interp.append(np.full_like(t_malla, np.nan))
        V2_interp.append(np.full_like(t_malla, np.nan))
        V3_interp.append(np.full_like(t_malla, np.nan))
        V4_interp.append(np.full_like(t_malla, np.nan))

V1_mean = np.nanmean(V1_interp, axis=0)
V1_std = np.nanstd(V1_interp, axis=0)
V2_mean = np.nanmean(V2_interp, axis=0)
V2_std = np.nanstd(V2_interp, axis=0)
V3_mean = np.nanmean(V3_interp, axis=0)
V3_std = np.nanstd(V3_interp, axis=0)
V4_mean = np.nanmean(V4_interp, axis=0)
V4_std = np.nanstd(V4_interp, axis=0)

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
# RESUMEN ESTADÍSTICO
# ============================================================
def t50(serie):
    idx = np.where(serie >= 2.5)[0]
    return t_malla[idx[0]] if len(idx) > 0 else np.nan

t50_vals = [t50(V1_mean), t50(V2_mean), t50(V3_mean), t50(V4_mean)]
t50_stds = [V1_std[np.where(V1_mean >= 2.5)[0][0]] if not np.isnan(t50_vals[0]) else np.nan,
            V2_std[np.where(V2_mean >= 2.5)[0][0]] if not np.isnan(t50_vals[1]) else np.nan,
            V3_std[np.where(V3_mean >= 2.5)[0][0]] if not np.isnan(t50_vals[2]) else np.nan,
            V4_std[np.where(V4_mean >= 2.5)[0][0]] if not np.isnan(t50_vals[3]) else np.nan]

print("\n" + "="*60)
print("📊 RESUMEN ESTADÍSTICO")
print("="*60)
print("Tiempos de subida al 50% (t50):")
for i in range(4):
    if not np.isnan(t50_vals[i]):
        print(f"  Nodo {i+1}: {t50_vals[i]:.2f} ± {t50_stds[i]:.3f} s")
    else:
        print(f"  Nodo {i+1}: No alcanza 2.5V en {DURACION} s")

idx_60 = np.argmin(np.abs(t_malla - 60))
print("\nVoltajes finales (t ≈ 60 s):")
for i, (mean, std) in enumerate(zip([V1_mean, V2_mean, V3_mean, V4_mean],
                                     [V1_std, V2_std, V3_std, V4_std])):
    print(f"  Nodo {i+1}: {mean[idx_60]:.3f} ± {std[idx_60]:.3f} V")
print("="*60)
print("✅ Procesamiento completado!")
