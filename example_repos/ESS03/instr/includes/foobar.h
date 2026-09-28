#ifndef FOOBAR_LIB_H
#define FOOBAR_LIB_H

/* Dummy helper library, demonstrating how C code placed in includes/ can be
   shared between all modes of an instrument. */

/* Returns 1 if the beamline number is valid for the given ESS sector ("N",
   "E", "S" or "W"), otherwise prints an error and returns 0. */
int foobar_valid_beamline( const char * sector, int beamline );

#endif
