/************************************************
 * 5-Channel Debounced Skin-to-Skin Touch Trigger
 * Touch Pins: D4, D6, D8, D10, D12
 * Baud Rate: 230400
 ************************************************/

const int touchPins[5] = {4, 6, 8, 10, 12};
unsigned long lastTouchTimes[5] = {0, 0, 0, 0, 0};
const unsigned long DEBOUNCE_DELAY = 600; // 600ms cooldown per wire

void setup() {
  Serial.begin(230400); // High-speed USB delivery
}

void loop() {
  unsigned long currentTime = millis();

  // Check each pin independently with double-verification
  for (int i = 0; i < 5; i++) {
    int pin = touchPins[i];

    // Read twice with a 1ms gap to filter out static noise / initial skin chatter
    if (isPinTouched(pin)) {
      delayMicroseconds(1000); 
      if (isPinTouched(pin)) {
        // Enforce cooldown per pin
        if (currentTime - lastTouchTimes[i] > DEBOUNCE_DELAY) {
          Serial.print("TOUCH_");
          Serial.println(i + 1); // Sends TOUCH_1 through TOUCH_5
          lastTouchTimes[i] = currentTime;
        }
      }
    }
  }
}

bool isPinTouched(int pin) {
  // 1. Discharge pin completely to GND
  pinMode(pin, OUTPUT);
  digitalWrite(pin, LOW);
  delayMicroseconds(5);

  // 2. Enable INPUT_PULLUP to charge pin to 5V
  pinMode(pin, INPUT_PULLUP);

  // 3. Wait 15 microseconds for skin-to-skin contact detection
  delayMicroseconds(15); 

  // Read state: LOW means skin contact detected!
  return (digitalRead(pin) == LOW);
}
