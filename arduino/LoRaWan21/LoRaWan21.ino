#include "LoRaWan_APP.h"

#include "mySHT31.h"

#include <Wire.h>
#include "HT_SSD1306Wire.h"


// mode OTAA
// Identifiants uniques générés dans TTN. Ils permettent au module de s’enregistrer sur le réseau.
uint8_t devEui[] = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08 };
uint8_t appEui[] = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08 };  // ou joinEUI
uint8_t appKey[] = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x0D0 };


// Variables ABP obligatoires pour éviter erreur de linkage
uint8_t nwkSKey[16] = { 0 };
uint8_t appSKey[16] = { 0 };
uint32_t devAddr = 0x00000000;


/*LoraWan channelsmask, default channels 0-7*/
// Le module utilise uniquement les canaux 0 à 7,
// ce qui est la configuration par défaut pour la bande EU868 utilisée en France.
// Les passerelles TTN écoutent généralement sur les canaux 0 à 7.
uint16_t userChannelsMask[6] = { 0x00FF, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000 };

/*LoraWan region, à selectionner dans le menu Tools*/
LoRaMacRegion_t loraWanRegion = ACTIVE_REGION;

/*LoraWan Class, Classe A et Classe C supportées*/
// classe A, qui est la plus courante et la plus économe en énergie dans le protocole LoRaWAN.
DeviceClass_t loraWanClass = CLASS_A;

/* Intervalle entre deux transmissions de message, valeur en millisecondes */
uint32_t appTxDutyCycle = 12 * 60000;  // soit 12 minutes

/*OTAA ou ABP*/
bool overTheAirActivation = true;  // Activation On-The-Air

/*ADR enable*/
// Adaptive Data Rate. En mettant loraWanAdr = true, on demande au module
// de laisser le réseau TTN optimiser automatiquement la vitesse de transmission et la puissance d’émission.
bool loraWanAdr = true;

/* Indicates if the node is sending confirmed or unconfirmed messages */
// Ddétermine si le module LoRaWAN demande un accusé de réception (ACK) pour chaque message envoyé.
// En mettant isTxConfirmed = true, on active le mode uplink confirmé (uplink : module Heltec vers réseau TTN),
// ce qui implique une communication bidirectionnelle avec le réseau TTN.
bool isTxConfirmed = true;

/* Application port */
// Définit le port d’application LoRaWAN utilisé pour transmettre le payload.
// En LoRaWAN, chaque message envoyé peut être associé à un port logique (appelé FPort)
// qui permet au serveur de savoir comment interpréter les données.
uint8_t appPort = 2;


/*!
* Nombre d'essais pour transmettre la trame, au cas où la couche LoRaMAC ne
* reçoit pas d'acquittement. La couche MAC opère une adaptation du datarate,
* selon les spécifications LoRaWAN V1.0.2, chapitre 18.4, d'après le tableau
* ci-dessous :
*
* Transmission nb | Data Rate
* ----------------|-----------
* 1 (first)       | DR
* 2               | DR
* 3               | max(DR-1,0)
* 4               | max(DR-1,0)
* 5               | max(DR-2,0)
* 6               | max(DR-2,0)
* 7               | max(DR-3,0)
* 8               | max(DR-3,0)
*
* Note : si le nombre d'essais est défini à 1 ou 2, la couche MAC ne diminuera
* pas le datarate si la couche LoRaMAC ne reçoit pas d'acquittement.
*/
// Configure le nombre de tentatives de retransmission pour les uplinks confirmés en LoRaWAN.
// Autrement dit, si le module envoie un message et ne reçoit pas d’accusé de réception (ACK) de TTN,
// il va réessayer jusqu’à 4 fois en diminuant le datarate avant d’abandonner.
uint8_t confirmedNbTrials = 4;

/* Préparation du payload de la trame */
static void prepareTxFrame(uint8_t port) {
  /*appData size is LORAWAN_APP_DATA_MAX_SIZE which is defined in "commissioning.h".
  *appDataSize max value is LORAWAN_APP_DATA_MAX_SIZE.
  *if enabled AT, don't modify LORAWAN_APP_DATA_MAX_SIZE, it may cause system hanging or failure.
  *if disabled AT, LORAWAN_APP_DATA_MAX_SIZE can be modified, the max value is reference to lorawan region and SF.
  *for example, if use REGION_CN470, 
  *the max value for different DR can be found in MaxPayloadOfDatarateCN470 refer to DataratesCN470 and BandwidthsCN470 in "RegionCN470.h".
  */
  appDataSize = 4;

  getRawDataSHT31();                          // Acquisition SHT31
  appData[0] = (rawTemperature >> 8) & 0xFF;  // octet poids fort
  appData[1] = rawTemperature & 0xFF;         // octet poids faible

  appData[2] = (rawHumidity >> 8) & 0xFF;  // octet poids fort
  appData[3] = rawHumidity & 0xFF;         // octet poids faible

  Serial.print(rawTemperature * (175.0 / 65535) - 45, 1);
  Serial.println("°C");
  Serial.print(rawHumidity * (100.0 / 65535), 1);
  Serial.println("%");
}

RTC_DATA_ATTR bool firstrun = true;

extern SSD1306Wire display;


void setup() {

  display.init();
  display.setContrast(255);  // valeur max : 0 à 255
  display.clear();
  display.drawString(0, 0, "LoRa Init...");
  display.display();


  initSHT31();

  Serial.begin(115200);
  Mcu.begin(HELTEC_BOARD, SLOW_CLK_TPYE);

  if (firstrun) {
    LoRaWAN.displayMcuInit();
    firstrun = false;
  }
}

void loop() {
  switch (deviceState) {
    case DEVICE_STATE_INIT:
      {
#if (LORAWAN_DEVEUI_AUTO)
        LoRaWAN.generateDeveuiByChipID();
#endif
        LoRaWAN.init(loraWanClass, loraWanRegion);
        //both set join DR and DR when ADR off
        LoRaWAN.setDefaultDR(3);
        break;
      }
    case DEVICE_STATE_JOIN:
      {
        LoRaWAN.displayJoining();
        LoRaWAN.join();
        break;
      }
    case DEVICE_STATE_SEND:
      {
        LoRaWAN.displaySending();
        prepareTxFrame(appPort);
        LoRaWAN.send();

        deviceState = DEVICE_STATE_CYCLE;
        break;
      }
    case DEVICE_STATE_CYCLE:
      {
        // Schedule next packet transmission
        txDutyCycleTime = appTxDutyCycle + randr(-APP_TX_DUTYCYCLE_RND, APP_TX_DUTYCYCLE_RND);
        LoRaWAN.cycle(txDutyCycleTime);
        deviceState = DEVICE_STATE_SLEEP;
        break;
      }
    case DEVICE_STATE_SLEEP:
      {
        LoRaWAN.displayAck();
        LoRaWAN.sleep(loraWanClass);
        break;
      }
    default:
      {
        deviceState = DEVICE_STATE_INIT;
        break;
      }
  }
}
