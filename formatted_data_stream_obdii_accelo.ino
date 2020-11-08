#include <mcp_can.h>
#include <mcp_can_dfs.h>
#include <SPI.h>
#include<Wire.h>
const int MPU=0x68; 


long unsigned int rxId;

unsigned long rcvTime;

unsigned char len = 0;
unsigned char buf[8];

int updateAccel = 0;


const int SPI_CS_PIN = 10;

double state_vector[8] = {0, 0, 0, 0, 0, 0, 0, 0};
// Time, RPM, vehicle speed, throttle percent, brake light, ax, ay, az (8 vars total)




MCP_CAN CAN(SPI_CS_PIN);                                    // Set CS pin

void setup()
{


    Wire.begin();
    Wire.beginTransmission(MPU);
    Wire.write(0x6B); 
    Wire.write(0);    
    Wire.endTransmission(true);

    
    Serial.begin(115200);
    

    while (CAN_OK != CAN.begin(CAN_500KBPS))
    {
        Serial.println("CAN BUS Module Failed to Initialized");
        Serial.println("Retrying....");
        delay(200);
    }    
    Serial.println("CAN BUS Module Initialized!");
    Serial.println("Time [ms], RPM, Velocity [mph], Throttle Percent [%], Brake Light Binary, AccelX [g's], AccelY [g's], AccelZ [g's]");    
}


void loop()
{
    
    if(CAN_MSGAVAIL == CAN.checkReceive())            // check if data coming
    {
        rcvTime = millis();
        CAN.readMsgBuf(&len, buf);    // read data,  len: data length, buf: data buf

        rxId= CAN.getCanId();


        if(rxId == 0x280){ // HEX 0x280, RPM and throttle pos
          state_vector[0] = rcvTime;
          state_vector[1] = (256*buf[3] + buf[2])/4.0; // RPM
          state_vector[3] = buf[5]/250.0*100.0; // throttle percent
          updateAccel = 1;
        }

        else if(rxId == 0x288){ // brake light
          state_vector[0] = rcvTime;
          if(buf[2] == 0x13){
            state_vector[4] = 1;
          }
          else if(buf[2] == 0x10){
            state_vector[4] = 0;
          }
          updateAccel = 1;
        }

        else if(rxId == 0x1A0){
          state_vector[0] = rcvTime;
          state_vector[2] = (256*buf[3] + buf[2]) / 180.0 / 1.60934; // mph
          updateAccel = 1;
        }


        //if we have a new can message for other data, we might as well update the accelos
        // on the same time stamp.

        if(updateAccel == 1){

          Wire.beginTransmission(MPU);
          Wire.write(0x3B);  
          Wire.endTransmission(false);
          Wire.requestFrom(MPU,12,true);  
          state_vector[5]=(Wire.read()<<8|Wire.read())/16384.0;    
          state_vector[6]=(Wire.read()<<8|Wire.read())/16384.0; 
          state_vector[7]=(Wire.read()<<8|Wire.read())/16384.0; 



          //print state vector
          for(int i = 0; i<8; i++){
            Serial.print(state_vector[i]);
            Serial.print("\t");
          }
          Serial.println();

        
          updateAccel = 0;
        }

    
    }

    
}
