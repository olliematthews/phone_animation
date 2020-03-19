# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 10:26:59 2020

@author: Ollie
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D, art3d, proj3d

def plot_axes(axis_points, ax):
    '''
    Plots the local axes on the plot.

    Parameters
    ----------
    axis_points : np.array 3x3
        The rotated unit vectors for the end of the axes.
    ax : plt.axis
        The axis on which to plot.

    Returns
    -------
    None.

    '''
    for i in range(3):
        end = axis_points[:,i]
        x = [0,end[0]]
        y = [0,end[1]]
        z = [0,end[2]]
        ax.plot3D(x,y,z)
        
def cuboid(coords, dims, color, **kwargs):
    '''
    Create a cuboid to represent the phone.

    Parameters
    ----------
    coords : np.array 3x3 of floats
        The coordinates of the end of each axis.
    dims : np.array [3,] of floats
        The dimensions of the phone.
    color : string
        Colour of the phone.
    **kwargs 

    Returns
    -------
    art3d.Poly3DCollection
        A cuboid representing the phone.

    '''
    
    pm = np.array([-1,1])
    sides = []
    
    # Get the direction vector for the phone.
    us = dims[None, :] * coords
    
    # Get each side (3 x 2 directions)
    for i in range(3):
        for direct in pm:
            center = direct * us[:,i] * 0.5
            j, k = [l for l in range(3) if not l == i]
            
            # Get the corners for each edge
            corners = []
            for directj, directk in zip([-1,-1,1,1] , [1,-1,-1,1]):
                corners.append(center + 0.5 * us[:,j] * directj + 0.5 * us[:,k] * directk)
            sides.append(corners)
            
    sides = np.array(sides).astype(float)
    return art3d.Poly3DCollection(sides, facecolors=np.repeat(color,6), **kwargs)
    
def plot_orientation(ax, orientation, dims):
    '''
    Plot the phone given an orientation.

    Parameters
    ----------
    ax : plt.axis
        Axis on which to plot.
    orientation : np.array [3,] of floats
        Orientation of the phone in alpha, beta, gamma (all in degrees).
    dims : np.array [3,] of floats
        The dimensions of the phone.
        
    Returns
    -------
    None.

    '''
    
    # Normal vectors for the global axes
    normals = np.array([[1,0,0],[0,1,0],[0,0,1]])
    
    orientation = np.deg2rad(orientation)
    
    ca, cb, cg = np.cos(orientation)
    sa, sb, sg = np.sin(orientation)
    
    # Correct for sign conventions
    sa = -sa
    sg = -sg
    
    # Get rotation matrix
    R = np.array([[ca * cb, ca * sb * sg - sa * cg, ca * sb * cg + sa * sg],
                  [sa * cb, sa * sb * sg + ca * cg, sa * sb * cg - ca * sg],
                  [-sb, cb * sg, cb * cg]])
    
    # Get local axis coordinates and phone cuboid
    coords = R @ normals
    pc = cuboid(coords, dims, color = 'black', alpha = 0.3)
    
    ax.clear()
    ax.add_collection3d(pc)    
    ax.set_xlim3d(-1.5, 1.5)
    ax.set_ylim3d(-1.5, 1.5)
    ax.set_zlim3d(-1.5, 1.5)
    plot_axes(coords, ax)
    
