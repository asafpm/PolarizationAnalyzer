import pygame, math
import numpy as np
import wireframe as wf

# Radian rotated by a key event
ROTATION_AMOUNT = np.pi/16
MOVEMENT_AMOUNT = 10

key_to_function = {
    pygame.K_LEFT:   (lambda x: x.transform(wf.translationMatrix(dx=-MOVEMENT_AMOUNT))),
    pygame.K_RIGHT:  (lambda x: x.transform(wf.translationMatrix(dx= MOVEMENT_AMOUNT))),
    pygame.K_UP:     (lambda x: x.transform(wf.translationMatrix(dy=-MOVEMENT_AMOUNT))),
    pygame.K_DOWN:   (lambda x: x.transform(wf.translationMatrix(dy= MOVEMENT_AMOUNT))),
    pygame.K_EQUALS: (lambda x: x.scale(1.25)),
    pygame.K_MINUS:  (lambda x: x.scale(0.8)),
    pygame.K_q:      (lambda x: x.rotate('x', ROTATION_AMOUNT)),
    pygame.K_w:      (lambda x: x.rotate('x',-ROTATION_AMOUNT)),
    pygame.K_a:      (lambda x: x.rotate('y', ROTATION_AMOUNT)),
    pygame.K_s:      (lambda x: x.rotate('y',-ROTATION_AMOUNT)),
    pygame.K_z:      (lambda x: x.rotate('z', ROTATION_AMOUNT)),
    pygame.K_x:      (lambda x: x.rotate('z',-ROTATION_AMOUNT))
}

light_movement = {
    pygame.K_q:      (lambda x: x.transform(wf.rotateXMatrix(-ROTATION_AMOUNT))),
    pygame.K_w:      (lambda x: x.transform(wf.rotateXMatrix( ROTATION_AMOUNT))),
    pygame.K_a:      (lambda x: x.transform(wf.rotateYMatrix(-ROTATION_AMOUNT))),
    pygame.K_s:      (lambda x: x.transform(wf.rotateYMatrix( ROTATION_AMOUNT))),
    pygame.K_z:      (lambda x: x.transform(wf.rotateZMatrix(-ROTATION_AMOUNT))),
    pygame.K_x:      (lambda x: x.transform(wf.rotateZMatrix( ROTATION_AMOUNT)))
}

class WireframeViewer(wf.WireframeGroup):
    """ A group of wireframes which can be displayed on a Pygame screen """
    
    def __init__(self, width, height, name="Wireframe Viewer"):
        self.width = width
        self.height = height
        
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(name)
        
        self.wireframes = {}
        self.wireframe_colours = {}
        self.object_to_update = []
        
        self.displayNodes = False
        self.displayEdges = True
        self.displayFaces = True
        
        self.perspective = 200. #False
        self.eyeX = self.width/2
        self.eyeY = 100
        self.view_vector = np.array([0, 0, -1])
        
        self.light = wf.Wireframe()
        self.light.addNodes([[0, -1, 0]])
        
        self.min_light = 0.02
        self.max_light = 1.0
        self.light_range = self.max_light - self.min_light 
        
        self.background = (10,10,50)
        self.nodeColour = (250,250,250)
        self.nodeRadius = 4
        
        self.control = 0
    
    def addWireframe(self, name, wireframe):
        self.wireframes[name] = wireframe
        #   If colour is set to None, then wireframe is not displayed
        self.wireframe_colours[name] = (250,250,250)
    
    def addWireframeGroup(self, wireframe_group):
        # Potential danger of overwriting names
        for name, wireframe in wireframe_group.wireframes.items():
            self.addWireframe(name, wireframe)
    
    def scale(self, scale):
        """ Scale wireframes in all directions from the centre of the group. """
        
        scale_matrix = wf.scaleMatrix(scale, self.width/2, self.height/2, 0)
        self.transform(scale_matrix)

    def rotate(self, axis, amount):
        (x, y, z) = self.findCentre()
        translation_matrix1 = wf.translationMatrix(-x, -y, -z)
        translation_matrix2 = wf.translationMatrix(x, y, z)
        
        if axis == 'x':
            rotation_matrix = wf.rotateXMatrix(amount)
        elif axis == 'y':
            rotation_matrix = wf.rotateYMatrix(amount)
        elif axis == 'z':
            rotation_matrix = wf.rotateZMatrix(amount)
            
        rotation_matrix = np.dot(np.dot(translation_matrix1, rotation_matrix), translation_matrix2)
        self.transform(rotation_matrix)

    def display(self):
        self.screen.fill(self.background)
        light = self.light.nodes[0][:3]
        spectral_highlight = self.light.nodes[0][:3] + self.view_vector
        spectral_highlight /= np.linalg.norm(spectral_highlight)
        
        for name, wireframe in self.wireframes.items():
            nodes = wireframe.nodes
            
            if self.displayFaces:
                for (face, colour) in wireframe.sortedFaces():
                    v1 = (nodes[face[1]] - nodes[face[0]])[:3]
                    v2 = (nodes[face[2]] - nodes[face[0]])[:3]
                    
                    normal = np.cross(v1, v2)
                    towards_us = np.dot(normal, self.view_vector)
                    
                    # Only draw faces that face us
                    if towards_us > 0:
                        normal /= np.linalg.norm(normal)
                        theta = np.dot(normal, light)
                        #catchlight_face = np.dot(normal, spectral_highlight) ** 25

                        c = 0
                        if theta < 0:
                            shade = self.min_light * colour
                        else:
                            shade = (theta * self.light_range + self.min_light) * colour
                        pygame.draw.polygon(self.screen, shade, [(nodes[node][0], nodes[node][1]) for node in face], 0)
                        
                        #mean_x = sum(nodes[node][0] for node in face) / len(face)
                        #mean_y = sum(nodes[node][1] for node in face) / len(face)
                        #pygame.draw.aaline(self.screen, (255,255,255), (mean_x, mean_y), (mean_x+25*normal[0], mean_y+25*normal[1]), 1)
            
            if self.displayEdges:
                colour = (0,255,0)
                for (n1, n2) in wireframe.edges:
                    if self.perspective:
                        if nodes[n1][2] > -self.perspective and nodes[n2][2] > -self.perspective:
                            z1 = self.perspective/ (self.perspective + nodes[n1][2])
                            x1 = self.width/2  + z1*(nodes[n1][0] - self.width/2)
                            y1 = self.height/2 + z1*(nodes[n1][1] - self.height/2)
                
                            z2 = self.perspective/ (self.perspective + nodes[n2][2])
                            x2 = self.width/2  + z2*(nodes[n2][0] - self.width/2)
                            y2 = self.height/2 + z2*(nodes[n2][1] - self.height/2)
                            
                            pygame.draw.aaline(self.screen, colour, (x1, y1), (x2, y2), 1)
                    else:
                        
                        pygame.draw.aaline(self.screen, colour, (nodes[n1][0], nodes[n1][1]), (nodes[n2][0], nodes[n2][1]), 1)

            if self.displayNodes:
                colour = (255,255,0)
                for node in nodes:
                    if self.perspective:
                        if node[2] > -self.perspective:
                            z = self.perspective/ (self.perspective + node[2])
                            x = self.width/2  + z*(node[0] - self.width/2)
                            y = self.height/2 + z*(node[1] - self.height/2)
                            pygame.draw.circle(self.screen, colour, (int(x), int(y)), self.nodeRadius, 0)
                    else:
                        pygame.draw.circle(self.screen, colour, (int(node[0]), int(node[1])), self.nodeRadius, 0)
        
        pygame.display.flip()

    def keyEvent(self, key):
        if key in key_to_function:
            key_to_function[key](self)
            #light_movement[key](self.light)

    def run(self):
        """ Display wireframe on screen and respond to keydown events """
        
        running = True
        key_down = False
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    key_down = event.key
                elif event.type == pygame.KEYUP:
                    key_down = None
            
            if key_down:
                self.keyEvent(key_down)
            
            self.display()
            self.update()
            
        pygame.quit()
