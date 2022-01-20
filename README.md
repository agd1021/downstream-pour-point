# downstream_pour_point
Python toolbox for ArcMap Desktop with example data

## Prepared for the peer-reviewed publication: 
Drayer, A. N., Guzy, J. C., & Price, S. J. (2020). Factors Influencing the Occupancy and Abundance of Streamside Salamander (<i>Ambystoma barbouri</i>) in Kentucky Streams. Journal of Herpetology, 54(3), 299-305. doi:10.1670/19-015

## Summary
To estimate the impact of land use and land cover on salamander occupancy along a stream network in Kentucky, herpetologists needed to measure percentage of land uses within local watersheds around survey point locations. A "local" watershed around a stream sampling site, in this case, was the watershed of all tributaries with a Strahler Order less than or equal to the Strahler Order of the sampled stream. The tool "DownstreamPourPoints" locates the confluence downstream of a survey site at which the Strahler Order increases along the given stream network. The output location can be used as a pour point to construct a local watershed.

## Algorithm
Returns a point feature class named output.
Given sites along a Strahler Ordered stream network,
1. validates that the stream network has necessary Strahler Order fields
2. creates an empty point feature class with field "Sites"
3. iterates through features of input parameters sites & swims downstream of each site to an endpoint where the Strahler Order of the stream network increases
5. adds those endpoints to the output point feature class

## Inputs
1. Sites: point layer of survey sites along a stream network
2. Strahler-Ordered stream network: Linear feature class of Strahler-Ordered streams. Must include 3 fields:
* "StrahlerOr": Integers
* "FROM_NODE": Integers indicating where line segments begin
* "TO_NODE": Integers indicating where line segments end
3. Output points: user-defined name of an output point feature class
4. Snap tolerance: Maximum allowable distance between input survey sites and input Strahler Ordered stream network.

## Output
Returns a point feature class.
