The 'create lines' code is based on the reported co-ordinates of vans as they move through the landscape of Samos, spraying pesticides. These co-ordinates are stored as X and Y co-ordinates in an excel file.

This code takes the co-ordinate points, and converts them into point geometries, then joins these into lines based on the date/time of the reported co-ordinates. 

It uses a customisable filter to filter out glitchy data, such as where co-ordinate data does not report for some time, so the van appears to 'fly' across the sea or mountains. 