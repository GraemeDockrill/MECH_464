#include "FastLED.h"

#define LED_PIN 3
#define NUM_LEDS 9
#define BRIGHTNESS 100

CRGB leds[NUM_LEDS];

void setup() {
  // put your setup code here, to run once:

  Serial.begin(9600);

  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
}

void loop() {
  // put your main code here, to run repeatedly:

  // wait for a serial message
  if(Serial.available()){

    int message = Serial.read();
    int LED = message & 0b00001111;
    int color = message >> 7;

    // check if LEDs are to be cleared
    if(LED == 9){
      for(int i = 0; i <= (NUM_LEDS - 1); i++){
          leds[i] = CRGB(0, 0, 0);
        }
    }
    // else change a single color
    else{
      // if computer or player color (computer == 1)
      if(color)
        leds[LED] = CRGB(BRIGHTNESS, 0, 0);
      else
        leds[LED] = CRGB(0, BRIGHTNESS, 0);
    }

  }

  // update LEDs
  FastLED.show();

  delay(10);
}
