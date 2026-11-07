const int PULSE_PIN = A0;
int threshold = 550; // Порог срабатывания оптического датчика BiTronics
unsigned long lastBeatTime = 0;
int bpm = 72;

void setup() {
  Serial.begin(9600);
}

void loop() {
  int val = analogRead(PULSE_PIN);
  unsigned long now = millis();

  // Детекция пика пульсовой волны (защита от дребезга 300 мс)
  if (val > threshold && (now - lastBeatTime > 300)) {
    unsigned long ibi = now - lastBeatTime; // Межпульсовой интервал
    lastBeatTime = now;
    int currentBpm = 60000 / ibi;
    if (currentBpm >= 45 && currentBpm <= 180) {
      bpm = (bpm * 0.7) + (currentBpm * 0.3); // Сглаживание
    }
  }

  // Каждые 500 мс отправляем данные в формате из ТЗ
  static unsigned long lastSend = 0;
  if (now - lastSend >= 500) {
    lastSend = now;
    Serial.print("BPM: ");
    Serial.println(bpm);
  }
}