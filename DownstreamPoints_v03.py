# Title: A. barbouri - finding downstream pour points
# Purpose: To generate pour-points along a stream network that can be used
# to construct local watersheds.
# Creator: Allison G. Davis, Laboratory Technician Senior
# University of Kentucky Department of Forestry and Natural Resources
# Created: 28 June 2017
# Last updated: 20 January 2022 1:30 PM
# -----------------------------------------------------------------------------

# Version notes
# -----------------------------------------------------------------------------
# v01 ran slow in IDLE and intolerably slow in ArcGIS
# v02 replaces MakeFeatureLayer functions with SelectByAttribute in the
#     in the iterator "Swimming downstream..."
# v02 collects less information about each stream segment in the SearchCursor
#     in the iterator "Swimming downstream..."
# v03 drops the final point at the FOR_NODE instead of the TO_NODE of the final
#     stream segment
# -----------------------------------------------------------------------------


import os
import arcpy
import random
import string

# Inputs
# -----------------------------------------------------------------------------
sites = arcpy.GetParameterAsText(0)
streams = arcpy.GetParameterAsText(1)
output = arcpy.GetParameterAsText(2)
tolerance = arcpy.GetParameterAsText(3)
# -----------------------------------------------------------------------------

# Test Inputs
# -----------------------------------------------------------------------------
##gdb = r"C:\Users\User\Documents\Price\A_barbouri\A_barbouri_watersheds.gdb"
##sites = "A_barbouri2017officialsites"
##streams = "drainage_line"
##tolerance = 1.0
##output = os.path.join(gdb, "downstream_pts")
##for fc in [sites, streams, tolerance, output]:
##    arcpy.Exists(fc)
# -----------------------------------------------------------------------------

def ValidateInputStreams( streams ):
    """
    Tests if input streams feature class has all the required fields.
    If it does, then returns stream layer.
    If not, returns False.
    """
    arcpy.AddMessage("Validating stream input...")
    fields = [f.name for f in arcpy.ListFields(streams)]  
    req_fields = ["OBJECTID", "StrahlerOr", "FROM_NODE", "TO_NODE"]

    if set(req_fields).issubset(fields):
        arcpy.AddMessage("\tInput stream network fields are compatible.")
        return True
    
    else:
        arcpy.AddError("\tInput stream network fields are not compatible.")
        return False

def DictionaryOfLayerFeatures( layer ):
    """
    Given an input layer with one feature, builds a dictionary of that
    feature's attribute table.
    """
    dictionary = {} 
    fields = [f.name for f in arcpy.ListFields(layer)]
    with arcpy.da.SearchCursor(layer, fields) as cursor:
        for row in cursor:
            for x in range(len(fields)):
                dictionary[fields[x]] = row[x]
    return dictionary

def FindDownstreamPoint(site_lyr, stream_lyr, tolerance):
    """
    Returns a list: [ site name, x_coord, y_coord ]

    Beginning at a site along streams, follows stream network until Strahler
    Order increases. Returns xy coordinates of the node where the site's
    stream joins an equally high or higher-Order stream.
    """

    arcpy.AddMessage("\tFinding nearest stream...")

    # Select closest input stream to input site
    arcpy.SelectLayerByLocation_management( stream_lyr, "INTERSECT",
                                            site_lyr, tolerance,
                                            "NEW_SELECTION")
    
    # Verify selection is unique
    matchcount = int( arcpy.GetCount_management(stream_lyr)[0] )
    if matchcount == 1:
        arcpy.AddMessage("\t\t{0} stream selected".format(matchcount,
                                                             tolerance))
        # arcpy.AddMessage("\t\tCreating feature layer...")
        start_segment = "start"
        arcpy.MakeFeatureLayer_management( stream_lyr, start_segment )
    else:
        arcpy.AddError("\t\tCould not find closest stream.")
        return False            

    # Build dictionary of starting segment attributes
    start = DictionaryOfLayerFeatures( start_segment ) 

    # Initialize downstream search
    StrOr_initial = start['StrahlerOr']
    arcpy.AddMessage( "\t\tInitial Strahler Order = " + str(start['StrahlerOr']))
    
    StrOr_current = StrOr_initial
    downstream_segments = [ start['OBJECTID'] ] # initialize list
    downstream_length = 0 # initialize measurement

    arcpy.AddMessage("\t\tSwimming downstream...")
    while StrOr_current == StrOr_initial:

        # Create new segment layer
        sql = "{0} = {1}".format("FROM_NODE", start['TO_NODE'])
        arcpy.SelectLayerByAttribute_management(stream_lyr, "NEW_SELECTION", sql)

        # Build dictionary of current downstream segment attributes
        downstream = DictionaryOfLayerFeatures( stream_lyr )              
        StrOr_current = downstream['StrahlerOr'] # Updates Strahler Order

        if StrOr_current == StrOr_initial:
            downstream_segments.append(downstream['OBJECTID']) # Update list
            downstream_length += downstream['Shape_Length'] # Sum distance
            start = downstream                              # Update start
            arcpy.AddMessage("\t\t\tJust keep swimming...")           
            
        elif StrOr_current > StrOr_initial:
            arcpy.AddMessage("\t\tFinal stream segment reached!")

            # New in v_03
            arcpy.AddMessage("\t\tBacktracking one stream segment...")
            sql = "{0} = {1}".format("OBJECTID", str(downstream_segments[-1]) )
            arcpy.SelectLayerByAttribute_management(
                stream_lyr, "NEW_SELECTION", sql)
            # -----------
            
            arcpy.AddMessage(
                "\t\t\tStrahler Order "+ str(downstream['StrahlerOr']) )
            arcpy.AddMessage(
                "\t\t\tTotal distance " + str(downstream_length) )
            # Total distance does not include length of higher Order segment
            
        else:
            arcpy.AddError("Final Strahler Order is less than initial!")
            return False

    arcpy.AddMessage("\t\tGetting coordinates of endpoint...")
    with arcpy.da.SearchCursor(stream_lyr, ['SHAPE@']) as cursor:
        for row in cursor:
            x_coord = row[0].firstPoint.X
            y_coord = row[0].firstPoint.Y
                
    arcpy.AddMessage( "\t\t\tX = {0}, Y = {1}".format(x_coord, y_coord) )

    return ( x_coord, y_coord )


def Main(sites, streams, tolerance, output):
    """
    Returns a point feature class named output.

    Given sites along a Strahler Ordered stream network,
    1. validates that the stream network has necessary Strahler Order fields
    2. creates an empty point feature class with field "Sites"
    3. iterates through features of input parameters sites & swims downstream
    of each site to an endpoint where the Strahler Order of the stream network
    increases
    5. adds those endpoints to the output point feature class

    Dependencies:
    import arcpy
    import os
    import random
    import string
    """
    
    arcpy.AddMessage( "Preparing data..." )
    
    output_directory = os.path.dirname(output)
    output_file = os.path.basename(output)
    arcpy.AddMessage( "\tOutput directory: " + str(output_directory) )
    arcpy.AddMessage( "\tOutput file: " + str(output_file) )

    arcpy.env.workspace = output_directory
    arcpy.env.overwriteOutput = True

    # Convert stream feature class to stream layer
    if ValidateInputStreams( streams ):
        stream_lyr = ''.join(random.choice(string.ascii_uppercase \
                                           + string.digits) for _ in range(7))
        arcpy.MakeFeatureLayer_management(streams, stream_lyr)
        arcpy.AddMessage("\tNumber of streams segments: " + \
              str(arcpy.GetCount_management(stream_lyr)[0]) ) # 369,133
    else:
        return False

    # Create output file
    arcpy.AddMessage( "Preparing results file.." )
    spatial_ref_fc = sites
    arcpy.CreateFeatureclass_management( output_directory, output_file,
                                         "POINT", '', '', '',
                                         spatial_ref_fc )
    arcpy.AddField_management( output, "Site", "TEXT", '', '', 50 )
    # print [f.name for f in arcpy.ListFields(output)]

    # Iterate through sites
    site_list = [ row[0] for row in arcpy.da.SearchCursor(sites, ['OID@'] ) ]
    arcpy.AddMessage("Site ID list: ")
    for s in site_list:
        arcpy.AddMessage(str(s))
    
    for s in site_list:
        
        # Starting point
        arcpy.AddMessage("\nSelecting site...")
        sql = "{0} = {1}".format('OBJECTID', s)
        arcpy.AddMessage("\tSelection query: " + str(sql) )
        site_lyr = str(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7)) )

        arcpy.MakeFeatureLayer_management(sites, site_lyr, sql)
        point_name = str([row[0]
                          for row in arcpy.da.SearchCursor(
                              site_lyr, ["Sites"] )][0]).replace(" ", "_")

        # Validate point selection
        matchcount = int( arcpy.GetCount_management(site_lyr)[0] )
        if matchcount == 1:
            arcpy.AddMessage("\t{0} site selected".format(point_name) )
        else:
            arcpy.AddError("MakeFeatureLayer of site {0} failed.".format(point_name) )
            return False             

        # Downstream analysis
        xy = FindDownstreamPoint(site_lyr, stream_lyr, tolerance)

        arcpy.AddMessage("\tWriting coordinates to output file...")
        cursor = arcpy.da.InsertCursor( output, ['SHAPE@XY', 'Site'] )
        cursor.insertRow( [ xy , point_name ] )
        del cursor

        # Move to next site
        arcpy.AddMessage("\tSite complete.")
        arcpy.Delete_management( site_lyr )

    arcpy.AddMessage("\nDone.")
    return output



# Run program
Main(sites, streams, tolerance, output)

    






    
