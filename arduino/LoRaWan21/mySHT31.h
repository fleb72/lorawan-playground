#ifndef MYSHT31_H
#define MYSHT31_H
#include <stdint.h>
#include "SHT31.h" // https://github.com/RobTillaart/SHT31


#define SHT31_ADDRESS   0x44

//GPIO41 (SDA), GPIO42 (SCL)
#define PIN_SDA 41
#define PIN_SCL 42

extern TwoWire myWire;
extern SHT31 sht;
extern uint16_t rawTemperature;
extern uint16_t rawHumidity;

void initSHT31(void);
void getRawDataSHT31(void);


#endif