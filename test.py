import math
import numpy as np
import wireframe as wf
import wireframeDisplay as wd
import basicShapes as shape

    
resolution = 20
viewer = wd.WireframeViewer(600, 400)
viewer.addWireframe('sphere', shape.Spheroid((300,300, 20), (160,160,160), resolution=resolution))

print "Create a sphere with %d faces." % len(viewer.wireframes['sphere'].faces)
viewer.displayEdges = True
viewer.displayNodes = True
viewer.displayFaces = False
viewer.run()
