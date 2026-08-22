// ============================================================
// SISTEMA RC 1×4 - OSCILOSCOPIO CON ARDUINO UNO
// ============================================================
// Autor: Fernando Mellado C.
// Descripción: Adquisición de datos con control por botón.
// Cada presión del botón inicia una medición de duración fija.
// ============================================================

const int PIN_CARGA = 12;
const int PIN_LED = 13;
const int PIN_BOTON = 2;
const int NUM_CANALES = 4;
const int PINES[NUM_CANALES] = {A0, A1, A2, A3};

const float V_REF = 5.0;
const int RESOLUCION = 1023;
const int INTERVALO_MUESTREO_MS = 50;
const unsigned long DURACION_MUESTREO_MS = 60000;

bool medicionActiva = false;
bool botonPresionado = false;
bool ultimoEstadoBoton = HIGH;
unsigned long ultimoDebounce = 0;
const unsigned long DEBOUNCE_DELAY = 50;

unsigned long tiempoInicio;
unsigned long contadorMuestras = 0;

void setup() {
  Serial.begin(115200);
  pinMode(PIN_CARGA, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BOTON, INPUT_PULLUP);
  digitalWrite(PIN_CARGA, LOW);
  digitalWrite(PIN_LED, LOW);
  for (int i = 0; i < NUM_CANALES; i++) {
    pinMode(PINES[i], INPUT);
  }
  Serial.println("=== SISTEMA RC - CONTROL POR BOTON ===");
  Serial.println("Presione el boton para INICIAR cada medicion");
  Serial.println("Duracion: 60 segundos");
}

void loop() {
  leerBoton();
  if (botonPresionado) {
    medicionActiva = !medicionActiva;
    if (medicionActiva) {
      digitalWrite(PIN_CARGA, HIGH);
      digitalWrite(PIN_LED, HIGH);
      tiempoInicio = millis();
      contadorMuestras = 0;
      Serial.println("INICIO_MEDICION");
    } else {
      digitalWrite(PIN_CARGA, LOW);
      digitalWrite(PIN_LED, LOW);
      Serial.println("FIN_MEDICION");
    }
    botonPresionado = false;
  }
  if (medicionActiva) {
    unsigned long tiempoActual = millis() - tiempoInicio;
    if (tiempoActual >= DURACION_MUESTREO_MS) {
      medicionActiva = false;
      digitalWrite(PIN_CARGA, LOW);
      digitalWrite(PIN_LED, LOW);
      Serial.println("FIN_MEDICION");
      Serial.println("=== MEDICION COMPLETADA (60 s) ===");
    } else {
      tomarMuestra();
    }
  }
}

void leerBoton() {
  int lectura = digitalRead(PIN_BOTON);
  if (lectura == LOW && ultimoEstadoBoton == HIGH) {
    if ((millis() - ultimoDebounce) > DEBOUNCE_DELAY) {
      botonPresionado = true;
      ultimoDebounce = millis();
    }
  }
  ultimoEstadoBoton = lectura;
}

void tomarMuestra() {
  unsigned long tiempoActual = millis() - tiempoInicio;
  float voltajes[NUM_CANALES];
  for (int i = 0; i < NUM_CANALES; i++) {
    voltajes[i] = analogRead(PINES[i]) * V_REF / RESOLUCION;
  }
  Serial.print(tiempoActual);
  Serial.print(",");
  for (int i = 0; i < NUM_CANALES; i++) {
    Serial.print(voltajes[i], 3);
    if (i < NUM_CANALES - 1) Serial.print(",");
  }
  Serial.print(",");
  Serial.println(digitalRead(PIN_LED));
  contadorMuestras++;
  delay(INTERVALO_MUESTREO_MS);
}
