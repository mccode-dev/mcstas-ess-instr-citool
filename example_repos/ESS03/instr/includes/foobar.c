#include "foobar.h"
#include <stdio.h>
#include <ctype.h>

int foobar_valid_beamline( const char * sector, int beamline )
{
  char s = (char)toupper( (unsigned char)sector[0] );
  int nmax;
  if ( s == 'N' || s == 'E' ) {
    nmax = 10;
  } else if ( s == 'S' || s == 'W' ) {
    nmax = 11;
  } else {
    fprintf( stderr, "ERROR: Invalid sector \"%s\" (must be N, E, S or W)\n", sector );
    return 0;
  }
  if ( beamline < 1 || beamline > nmax ) {
    fprintf( stderr, "ERROR: Invalid beamline %i for sector %c (must be 1..%i)\n",
             beamline, s, nmax );
    return 0;
  }
  return 1;
}
