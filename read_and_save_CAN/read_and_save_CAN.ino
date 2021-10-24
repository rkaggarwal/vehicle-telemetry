#include <FlexCAN_T4.h>
#include <SD.h>
#include <SPI.h>

FlexCAN_T4<CAN1, RX_SIZE_256, TX_SIZE_16> can1;
CAN_message_t can1Msg;

int LED_PIN    = 31; // LED indicating data is being recorded
int BUTTON_PIN = 32; // button for recording data

int state = -1; // state machine (-1: NA, 0: STARTUP, 1: IDLE, 2: IDLE->REC, 3: REC, 4: REC->IDLE)
int numberOfSwitches          = 0;
int time_of_last_button_press = 0;



String datalogname = "LOG12.txt"; // put whatever name you want in here
bool SDcardExists = 0;
String can_msg_for_sd = "";
const int chipSelect = BUILTIN_SDCARD;
File dataFile = File();


///////////////////////////////


void setup () {

  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), buttonPress_ISR, FALLING); // pin goes low when button is pressed
  state = 0; // initialize state in startup
  time_of_last_button_press = millis();

  can1.begin();
  can1.setBaudRate(500000); // baud rate of car
  can1.enableFIFO(); // enable FIFO buffer of messages
  can1.enableFIFOInterrupt(); // use interrupt-driven parsing
  can1.onReceive(readCANMessage); // function to call once a new message is received

  Serial.begin(115200);
  while (!Serial) {
    ;  // wait for serial port to connect
  }
  Serial.println("CAN Bus Initialized!");


  Serial.print("Initializing SD card...");
  if (!SD.begin(chipSelect)) {
    SDcardExists = 0;
    Serial.println("SD card not initialized.");
  }
  else {
    SDcardExists = 1;
    Serial.println("SD card initialized!");
  }
}


void writeStringToSD(String msg_to_write) {
  if (state == 3) { // make sure we're in the recording state
    if (dataFile) {
      Serial.println(msg_to_write);
      dataFile.println(msg_to_write);
    }
    else {
      Serial.println("Could not open file!");
    }
  }
}



void readCANMessage(const CAN_message_t &msg) {

  // reads and prints a can message, called whenever a new CAN message is received
  // we expect 8 bytes per CAN message
  can_msg_for_sd = "";
  //char msgBuffer [2*msg.len] = {}; // 2 HEX chars per byte
  
  can_msg_for_sd += String(millis()) + ", "
                  + String(msg.id, HEX) + ", "
                  + String(msg.len) + ", " // length in bytes
                  + String(msg.flags.overrun) + ", "
                  + String(msg.flags.extended) + ", ";
                  
  for (uint8_t i = 0; i < msg.len; i++) {
    char dataString[2] = {};
    sprintf(dataString, "%02X", msg.buf[i]);
    can_msg_for_sd += String(dataString);
    //can_msg_for_sd += String(msg.buf[i], HEX);
  }


//  char dataString[50] = {0};
//  sprintf(dataString,"%02X:%02X:%02X:%02X:%02X:%02X",mac[0],mac[1],mac[2],mac[3],mac[4],mac[5]);
  Serial.println(can_msg_for_sd); // see what we're reading!
  writeStringToSD(can_msg_for_sd); // write the message to the datalog.

}

void loop () {
  can1.events(); // initialize the can1 bus

  //Serial.println(state);
  switch (state) {
    case 0: // STARTUP
      state = 1;
      break;

    case 1: // IDLE
      break;

    case 2: // IDLE to RECORDING (rest stop)
      dataFile = SD.open(datalogname.c_str(), FILE_WRITE);
      digitalWrite(LED_PIN, HIGH);
      state = 3;
      writeStringToSD("Time [ms], ID [HEX], Length [Bytes], Flag (Overrun), Flag (Extended), Message [HEX]\n");
      break;

    case 3: // RECORDING
      // When a new message is received the can bus read method will
      // automatically record if the state is 3.
      break;

    case 4: // RECORDING to IDLE (rest stop)
      dataFile.close();
      digitalWrite(LED_PIN, LOW);
      state = 1;
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
    //Serial.println(time_of_last_button_press);
    //Serial.println(state);

    switch (state) {
      case 1:
        // then go from IDLE -> rest stop before RECORDING
        state = 2;

      case 2:
        break;
        
      case 3:
        // then go from RECORDING -> rest stop before IDLE
        state = 4;

      case 4:
        break;

      default:
        break;
    }
  }
}
