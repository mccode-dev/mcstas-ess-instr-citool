"""Database of the instrument model repositories at DMSC (in the group
dmsc-instrumentmodels at git.esss.dk), which use (or are being moved to) the
standard layout checked by this tool.

The workflow .github/workflows/instrument-repos.yml tests them with the
current version of the tool, and the documentation lists them. Please keep
the entries up to date, in particular "standard_layout" when a repository is
moved to the standard layout.
"""

GITLAB_GROUP_URL = "https://git.esss.dk/dmsc-instrumentmodels"

# Fields of each entry:
#   name:            name of the instrument (or of the repository)
#   repo:            name of the repository in the GitLab group
#   description:     short description
#   standard_layout: True if the default branch follows the standard layout
#                    (i.e. "mcstas-ess-instr-citool -a runci" is expected to
#                    pass), False if it is not (yet) moved to it
#   public:          True if the repository can be cloned without logging in
REPOS = [
    dict( name = "BEER", repo = "beer",
          description = "Engineering diffractometer",
          standard_layout = False, public = False ),
    dict( name = "ESTIA", repo = "estia",
          description = "Polarised neutron reflectometer",
          standard_layout = False, public = False ),
    dict( name = "FREIA", repo = "freia",
          description = "Liquid interfaces reflectometer",
          standard_layout = True, public = False ),
    dict( name = "HEIMDAL", repo = "heimdal",
          description = "Hybrid diffractometer",
          standard_layout = False, public = False ),
    dict( name = "LOKI", repo = "LOKI",
          description = "Broadband small-angle neutron scattering",
          standard_layout = True, public = True ),
    dict( name = "MAGiC", repo = "magic",
          description = "Magnetism single crystal diffractometer",
          standard_layout = False, public = True ),
    dict( name = "NMX", repo = "nmx",
          description = "Macromolecular diffractometer",
          standard_layout = False, public = True ),
    dict( name = "ODIN", repo = "odin",
          description = "Multi-purpose imaging",
          standard_layout = True, public = True ),
    dict( name = "SKADI", repo = "skadi",
          description = "Small-angle neutron scattering",
          standard_layout = True, public = True ),
    dict( name = "T-REX", repo = "t-rex",
          description = "Bispectral direct geometry spectrometer",
          standard_layout = False, public = False ),
    dict( name = "TBL", repo = "tbl",
          description = "Test beamline",
          standard_layout = True, public = True ),
    dict( name = "Template", repo = "ess-instrument-template",
          description = "Template for new instrument repositories",
          standard_layout = True, public = True ),
]


def repos():
    """The repositories, as a list of dictionaries (the fields above, and
    "url", the URL of the repository)."""
    return [ dict( r, url = f"{GITLAB_GROUP_URL}/{r['repo']}" )
             for r in REPOS ]


def print_table( file = None ):
    rows = [ ( r["name"], r["description"],
               "yes" if r["standard_layout"] else "no",
               "yes" if r["public"] else "no", r["url"] )
             for r in repos() ]
    header = ( "Name", "Description", "Standard layout", "Public", "URL" )
    widths = [ max(len(row[i]) for row in rows + [header])
               for i in range(len(header)) ]
    for row in [ header, tuple("-" * w for w in widths) ] + rows:
        print( "  ".join(c.ljust(w) for c, w in zip(row, widths, strict=True))
               .rstrip(), file = file )
