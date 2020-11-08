#include <FlexCAN_T4.h>

FlexCAN_T4<CAN1, RX_SIZE_256, TX_SIZE_16> can1;
CAN_message_t can1Msg;

int LED_PIN = 31;
int BUTTON_PIN = 32;

int state = -1;
// state dictionary:
// -1: NA
// 0: STARTUP
// 1: IDLE
// 2: RECORDING

int numberOfSwitches = 0;
int time_of_last_button_press = 0;

///////////////////////////////


void setup () {

  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), buttonPress_ISR, FALLING);
  state = 0;
  time_of_last_button_press = millis();


  can1.begin();
  can1.setBaudRate(500000);
  Serial.begin(115200);
}




void loop () {

  // Let's read our CAN received messages
  if ( can1.read(msg) ) {
    Serial.print("CAN1 ");
    Serial.print("MB: "); Serial.print(msg.mb);
    Serial.print("  ID: 0x"); Serial.print(msg.id, HEX );
    Serial.print("  EXT: "); Serial.print(msg.flags.extended );
    Serial.print("  LEN: "); Serial.print(msg.len);
    Serial.print(" DATA: ");
    for ( uint8_t i = 0; i < 8; i++ ) {
      Serial.print(msg.buf[i]); Serial.print(" ");
    }
    Serial.print("  time: "); Serial.println(msg.timestamp);
  }

  Serial.print("Number of Button Presses: ");
  Serial.println(numberOfSwitches);

  switch (state) {

    case 0:
      // STARTUP
      state = 1;
      break;

    case 1:
      // IDLE

      break;

    case 2:
      // RECORDING

      // blink the LED
      digitalWrite(LED_PIN, HIGH);
      delay(25);
      digitalWrite(LED_PIN, LOW);
      delay(25);

      break;

    default:
      break;


  }
}


void buttonPress_ISR() {
  // Button de-bouncing hack.  Should really fix this in hardware w/ an RC-filter...
  if (millis() - time_of_last_button_press > 2000) {
    time_of_last_button_press = millis();
    numberOfSwitches++;

    if (state == 1) {
      // then start recording
      state = 2;
    }

    else {
      // then stop recording
      state = 1;
      digitalWrite(LED_PIN, LOW);
    }
  }
}



static void hexDump(uint8_t dumpLen, uint8_t *bytePtr)
{
  uint8_t working;
  while ( dumpLen-- ) {
    working = *bytePtr++;
    Serial.write( hex[ working >> 4 ] );
    Serial.write( hex[ working & 15 ] );
  }
  Serial.write('\r');
  Serial.write('\n');
}
