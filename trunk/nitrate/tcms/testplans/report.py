# -*- coding: utf-8 -*-
# 
# Nitrate is copyright 2010 Red Hat, Inc.
# 
# Nitrate is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version. This program is distributed in
# the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranties of TITLE, NON-INFRINGEMENT,
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# 
# The GPL text is available in the file COPYING that accompanies this
# distribution and at <http://www.gnu.org/licenses>.
# 
# Authors:
#   David Malcolm <dmalcolm@redhat.com>

class Axis:
    """
    Represents one of the two axis used to build a table.

    - attrName : attribute used in objects
    - desc : human-readable description of the axis
    - headingMaker: function for turning row/column objects into human-readable text
    - comparator: function for comparing objects
    """
    def __init__(self, attrName, desc, headingMaker, comparator = None):
        self.attrName = attrName
        self.desc = desc
        self.headingMaker = headingMaker
        self.comparator = comparator        

class Report:
    """
    Organize a collection of objects into a 2-dimensional grid, ready tp
    be rendered as an HTML table.

    Picks coordinates for each objects based on two attributes.
      - objs: sequence of objects
      - xAxis: name of object attribute used for determining its x-coord in grid
      - yAxis: name of object attribute used for determining its y-coord in grid
      - cellRenderer: function to turn a list of objects into a fragment of HTML
    """
    def __init__(self, objs, xAxis, yAxis, cellRenderer):
        self.objs = objs
        self.xAxis = xAxis
        self.yAxis = yAxis
        self.cellRenderer = cellRenderer

        # Generate:
        #  cellDict, a dictionary: from (col, row) pairs -> lists of objects
        #  rows/cols = sets of row/col values
        self.cellDict = {}
        self.rows = {}
        self.cols = {}
        
        for obj in objs:
            coord = self.get_coord_of(obj)
            (col, row) = coord

            #print col
            #print row
            self.cols[col] = col
            self.rows[row] = row
            
            if coord in self.cellDict:
                self.cellDict[coord].append(obj)
            else:
                self.cellDict[coord] = [obj]

        # convert dicts to sorted lists:
        #print self.cols.keys()
        #print self.rows.keys()
        self.cols = sorted(self.cols.keys(), self.xAxis.comparator)
        self.rows = sorted(self.rows.keys(), self.yAxis.comparator)

        # Generate a list of lists of HTML fragments
        # We will use this to build an HTML table
        self.html_rows = []
        for row in self.rows:
            html_row = [self.yAxis.headingMaker(row)]
            for col in self.cols:
                html_row.append(self.cellRenderer(self.get_objs_at(col, row)))
            self.html_rows.append(html_row)

    def get_coord_of(self, obj):
        """
        Get the (x,y) coordinate of the given object
        """
        return (getattr(obj, self.xAxis.attrName),
                getattr(obj, self.yAxis.attrName))

    def column_headings(self):
        return [self.xAxis.headingMaker(col) for col in self.cols]

    def get_objs_at(self, row, col):
        coord = (row, col)
        #print coord
        #print self.cellDict
        if coord in self.cellDict:
            return self.cellDict[coord]
        else:
            return []
