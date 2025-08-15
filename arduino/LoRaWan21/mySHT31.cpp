#include "mySHT31.h"


TwoWire myWire(1);  // I2C1
SHT31 sht(SHT31_ADDRESS, &myWire);  // capteur à l'adresse 0x44
uint16_t rawTemperature;
uint16_t rawHumidity;

void initSHT31() {
  myWire.begin(PIN_SDA, PIN_SCL);
  myWire.setClock(100000);  // 100 kHz

  sht.begin();
}

void getRawDataSHT31(void) {
  sht.requestData();
  delay(50);

  if (sht.dataReady()) {
    bool success = sht.readData();

    if (!success) {
      Serial.println("Échec de lecture");
    } else {
      rawTemperature = sht.getRawTemperature();
      rawHumidity = sht.getRawHumidity();
    }
  }
}
