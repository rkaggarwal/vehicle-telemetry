#include <mcp_can.h>
#include <mcp_can_dfs.h>
#include <SPI.h>


long unsigned int rxId;

unsigned long rcvTime;

unsigned char len = 0;
unsigned char buf[8];


const int SPI_CS_PIN = 10;


MCP_CAN CAN(SPI_CS_PIN);                                    // Set CS pin

void setup()
{
    Serial.begin(115200);
    

    while (CAN_OK != CAN.begin(CAN_500KBPS))
    {
        Serial.println("CAN BUS Module Failed to Initialized");
        Serial.println("Retrying....");
        delay(200);
    }    
    Serial.println("CAN BUS Module Initialized!");
   // Serial.println("Time, CH1, CH2, CH3, CH4, CH5, CH6, CH7, CH8, CH9, CH10, CH11, CH12, CH13, CH14, CH15, CH16, CH17");    
}


void loop()
{
    
    if(CAN_MSGAVAIL == CAN.checkReceive())            // check if data coming
    {
        rcvTime = millis();
        CAN.readMsgBuf(&len, buf);    // read data,  len: data length, buf: data buf

        rxId= CAN.getCanId();

        Serial.print(rcvTime);
        Serial.print("\t\t");
        Serial.print("0x");
        Serial.print(rxId, HEX);
        Serial.print("\t");

        for(int i = 0; i<len; i++)    // print the data in hex
        {
            if(buf[i] > 15){
              Serial.print("0x");
              Serial.print(buf[i], HEX);    
            }
          else{
              Serial.print("0x0");
              Serial.print(buf[i], HEX);
          }  

            
            //Serial.print("0x");
            //Serial.print(buf[i], HEX);
            
            Serial.print("\t");            
        }

        // pad with additional tabs if numBytes is less than 8

        for(int i = 0; i<8-len; i++){
          Serial.print("\t");
        }


        for(int i = 0; i<len; i++)    // print the data in DEC
        {
            Serial.print(buf[i], DEC);

            
            //Serial.print("0x");
            //Serial.print(buf[i], HEX);
            
            Serial.print("\t");            
        }




        
        Serial.println();

        


        
    }
}
