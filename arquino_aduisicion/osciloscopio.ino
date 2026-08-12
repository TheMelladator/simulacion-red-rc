// Sistema RC con 4 capacitores - CONTROL TOGGLE
// Botón: Inicia/Pausa la medición
// R = 33kΩ, C = 100μF
// Alimentación desde Arduino (5V) - SIN DIVISORES

const int PIN_CARGA = 12;      // Pin que alimenta los capacitores
const int PIN_LED = 13;        // Pin para el LED indicador
const int PIN_BOTON = 2;       // Pin para el botón de control

const int NUM_CANALES = 4;
const int PINES[NUM_CANALES] = {A0, A1, A2, A3};
const float V_REF = 5.0;       // Ajustar según medición real
const int RESOLUCION = 1023;

const int INTERVALO_MUESTREO_MS = 50;  // 50ms = 20 muestras/segundo

// Estados del sistema
bool medicionActiva = false;      // TRUE = midiendo, FALSE = detenido
bool botonPresionado = false;
bool ultimoEstadoBoton = HIGH;    // Para detectar flancos
unsigned long ultimoDebounce = 0;
const unsigned long DEBOUNCE_DELAY = 50;  // 50ms anti-rebote

unsigned long tiempoInicio;
int contadorMuestras = 0;

void setup() {
  Serial.begin(115200);
  
  // Configurar pines
  pinMode(PIN_CARGA, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BOTON, INPUT_PULLUP);  // Pull-up interno activado
  
  // Inicializar
  digitalWrite(PIN_CARGA, LOW);
  digitalWrite(PIN_LED, LOW);
  
  // Configurar pines analógicos
  for (int i = 0; i < NUM_CANALES; i++) {
    pinMode(PINES[i], INPUT);
  }
  
  Serial.println("=== SISTEMA RC - CONTROL TOGGLE ===");
  Serial.println("Presione el botón para INICIAR/DETENER la medición");
  Serial.println("tiempo_ms,C1_voltaje,C2_voltaje,C3_voltaje,C4_voltaje,LED_estado");
}

void loop() {
  // Leer estado del botón (detección de flanco)
  leerBoton();
  
  // Si se presionó el botón, toggle el estado
  if (botonPresionado) {
    medicionActiva = !medicionActiva;  // Cambiar estado
    
    if (medicionActiva) {
      // INICIAR MEDICIÓN
      digitalWrite(PIN_CARGA, HIGH);    // Comenzar carga
      digitalWrite(PIN_LED, HIGH);      // Encender LED
      tiempoInicio = millis();
      contadorMuestras = 0;
      Serial.println("INICIO_MEDICION");
    } else {
      // DETENER MEDICIÓN
      digitalWrite(PIN_CARGA, LOW);     // Detener carga
      digitalWrite(PIN_LED, LOW);       // Apagar LED
      Serial.println("FIN_MEDICION");
      Serial.println("=== MEDICIÓN DETENIDA ===");
    }
    
    botonPresionado = false;  // Resetear flag
  }
  
  // Si la medición está activa, tomar muestras
  if (medicionActiva) {
    tomarMuestra();
  }
}

// --- FUNCIONES ---

void leerBoton() {
  int lectura = digitalRead(PIN_BOTON);
  
  // Detectar flanco de bajada (botón presionado)
  if (lectura == LOW && ultimoEstadoBoton == HIGH) {
    // Anti-rebote
    if ((millis() - ultimoDebounce) > DEBOUNCE_DELAY) {
      botonPresionado = true;
      ultimoDebounce = millis();
    }
  }
  
  ultimoEstadoBoton = lectura;
}

void tomarMuestra() {
  // Calcular tiempo transcurrido
  unsigned long tiempoActual = millis() - tiempoInicio;
  
  // Leer los 4 canales
  float voltajes[NUM_CANALES];
  for (int i = 0; i < NUM_CANALES; i++) {
    int valorADC = analogRead(PINES[i]);
    voltajes[i] = (valorADC * V_REF) / RESOLUCION;
  }
  
  // Enviar datos por serial
  Serial.print(tiempoActual);
  Serial.print(",");
  for (int i = 0; i < NUM_CANALES; i++) {
    Serial.print(voltajes[i], 3);
    if (i < NUM_CANALES - 1) Serial.print(",");
  }
  Serial.print(",");
  Serial.println(digitalRead(PIN_LED));
  
  contadorMuestras++;
  
  // Esperar hasta el siguiente intervalo
  delay(INTERVALO_MUESTREO_MS);
}