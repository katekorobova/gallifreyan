import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle

# Function to draw a circle
def draw_circle(ax, center, radius, **kwargs):
    circle = Circle(center, radius, **kwargs)
    ax.add_artist(circle)

# Function to draw an arc
def draw_arc(ax, center, radius, theta1, theta2, **kwargs):
    arc = Arc(center, 2*radius, 2*radius, angle=0, theta1=theta1, theta2=theta2, **kwargs)
    ax.add_artist(arc)

# Function to draw lines
def draw_line(ax, start, end, **kwargs):
    line = plt.Line2D((start[0], end[0]), (start[1], end[1]), **kwargs)
    ax.add_line(line)

# Setup the plot
fig, ax = plt.subplots(figsize=(10, 10))
ax.set_aspect('equal')
ax.set_axis_off()

# Draw circles
draw_circle(ax, (0, 0), 1, color='black', fill=False, linewidth=2)
draw_circle(ax, (0, 0), 1.5, color='black', fill=False, linewidth=2)
draw_circle(ax, (2, 2), 1, color='black', fill=False, linewidth=2)
draw_circle(ax, (-2, -2), 1, color='black', fill=False, linewidth=2)
draw_circle(ax, (2, -2), 1, color='black', fill=False, linewidth=2)

# Adding arcs
draw_arc(ax, (0, 0), 1.25, 0, 180, color='black', linewidth=2)
draw_arc(ax, (0, 0), 1.75, 180, 360, color='black', linewidth=2)
draw_arc(ax, (2, 2), 0.75, 45, 225, color='black', linewidth=2)
draw_arc(ax, (-2, -2), 0.75, 225, 45, color='black', linewidth=2)
draw_arc(ax, (2, -2), 0.75, 135, 315, color='black', linewidth=2)

# Adding lines
draw_line(ax, (-3, 0), (3, 0), color='black', linewidth=2)
draw_line(ax, (0, -3), (0, 3), color='black', linewidth=2)
draw_line(ax, (-2, -2), (2, 2), color='black', linewidth=2)
draw_line(ax, (-2, 2), (2, -2), color='black', linewidth=2)

# Adding more circles inside the existing ones
draw_circle(ax, (0, 0), 0.5, color='black', fill=False, linewidth=2)
draw_circle(ax, (2, 2), 0.5, color='black', fill=False, linewidth=2)
draw_circle(ax, (-2, -2), 0.5, color='black', fill=False, linewidth=2)
draw_circle(ax, (2, -2), 0.5, color='black', fill=False, linewidth=2)

# Adding small arcs inside the existing circles
draw_arc(ax, (0, 0), 0.5, 90, 270, color='black', linewidth=2)
draw_arc(ax, (2, 2), 0.5, 0, 180, color='black', linewidth=2)
draw_arc(ax, (-2, -2), 0.5, 180, 360, color='black', linewidth=2)
draw_arc(ax, (2, -2), 0.5, 270, 90, color='black', linewidth=2)

# Show the plot
plt.show()