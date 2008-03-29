"""
Data sources classes and their associated functions for mlab.
"""

# Author: Gael Varoquaux <gael.varoquaux@normalesup.org>
# Copyright (c) 2007, Enthought, Inc. 
# License: BSD Style.

from enthought.mayavi.sources.array_source import ArraySource
import numpy
import tools
from enthought.tvtk.tools import mlab
from enthought.tvtk.api import tvtk

__all__ = [ 'vectorscatter', 'vectorfield', 'scalarscatter', 'scalarfield',
    'linesource', 'array2dsource', 'gridsource',
]

def _make_glyph_data(points, vectors=None, scalars=None):
    """Makes the data for glyphs using mlab.
    """
    g = mlab.Glyphs(points, vectors, scalars)
    return g.poly_data

############################################################################
# Argument processing
############################################################################

def process_regular_vectors(*args):
    """ Converts different signatures to (x, y, z, u, v, w). """
    if len(args)==3:
        u, v, w = args
        assert len(u.shape)==3, "3D array required"
        x, y, z = numpy.indices(u.shape)
    elif len(args)==6:
        x, y, z, u, v, w = args
    elif len(args)==4:
        x, y, z, f = args
        if not callable(f):
            raise ValueError, "When 4 arguments are provided, the fourth must be a callable"
        u, v, w = f(x, y, z)
    else:
        raise ValueError, "wrong number of arguments"

    assert ( x.shape == y.shape and
            y.shape == z.shape and
            u.shape == z.shape and
            v.shape == u.shape and
            w.shape == v.shape ), "argument shape are not equal"

    return x, y, z, u, v, w

def process_regular_scalars(*args):
    """ Converts different signatures to (x, y, z, s). """
    if len(args)==1:
        s = args[0]
        assert len(s.shape)==3, "3D array required"
        x, y, z = numpy.indices(s.shape)
    elif len(args)==3:
        x, y, z = args
        s = None 
    elif len(args)==4:
        x, y, z, s = args
        if callable(s):
            s = s(x, y, z)
    else:
        raise ValueError, "wrong number of arguments"

    assert ( x.shape == y.shape and
            y.shape == z.shape and
            ( s == None
                or s.shape == z.shape ) ), "argument shape are not equal"

    return x, y, z, s

def process_regular_2d_scalars(*args):
    """ Converts different signatures to (x, y, s). """
    if len(args)==1:
        s = args[0]
        assert len(s.shape)==2, "2D array required"
        x, y = numpy.indices(s.shape)
    elif len(args)==3:
        x, y, s = args
        if callable(s):
            s = s(x, y)
    else:
        raise ValueError, "wrong number of arguments"

    assert ( x.shape == y.shape and
                s.shape == y.shape ), "argument shape are not equal"

    return x, y, s


############################################################################
# Sources 
############################################################################

def vectorscatter(*args, **kwargs):
    """ Creates scattered vector data. 
    
    **Function signatures**::

        vectorscatter(u, v, w, ...)
        vectorscatter(x, y, z, u, v, w, ...)
        vectorscatter(x, y, z, f, ...)

    If only 3 arrays u, v, w are passed the x, y and z arrays are assumed to be
    made from the indices of vectors.

    If 4 positional arguments are passed the last one must be a callable, f, 
    that returns vectors.

    **Keyword arguments**:
    
        :name: the name of the vtk object created.

        :scalars: optional scalar data."""
    x, y, z, u, v, w = process_regular_vectors(*args)

    points = numpy.c_[x.ravel(), y.ravel(), z.ravel()]
    vectors = numpy.c_[u.ravel(), v.ravel(), w.ravel()]
    scalars = kwargs.pop('scalar', None)
    name = kwargs.pop('name', 'VectorScatter')

    data_source = _make_glyph_data(points, vectors, scalars)
    return tools._add_data(data_source, name)


def vectorfield(*args, **kwargs):
    """ Creates vector field data. 
    
    **Function signatures**::

        vectorsfield(u, v, w, ...)
        vectorsfield(x, y, z, u, v, w, ...)
        vectorsfield(x, y, z, f, ...)

    If only 3 arrays u, v, w are passed the x, y and z arrays are assumed to be
    made from the indices of vectors.

    If the x, y and z arrays are passed they are supposed to have been
    generated by `numpy.mgrid`. The function builds a scalar field assuming 
    the points are regularily spaced.

    If 4 positional arguments are passed the last one must be a callable, f, 
    that returns vectors.

    **Keyword arguments**:
        
        :name: the name of the vtk object created.

        :scalars: optional scalar data."""
    x, y, z, u, v, w = process_regular_vectors(*args)

    dx = x[1, 0, 0] - x[0, 0, 0]
    dy = y[0, 1, 0] - y[0, 0, 0]
    dz = z[0, 0, 1] - z[0, 0, 0]

    vectors = numpy.concatenate([u[..., numpy.newaxis],
                            v[..., numpy.newaxis],
                            w[..., numpy.newaxis] ],
                            axis=3)
                            
    scalars = kwargs.pop('scalars', None)
    kwargs = {}
    if scalars is not None:
        kwargs['scalar_data'] = scalars
        
    data_source = ArraySource(transpose_input_array=True,
                    vector_data=vectors,
                    origin=[x.min(), y.min(), z.min()],
                    spacing=[dx, dy, dz],
                    **kwargs)

    name = kwargs.pop('name', 'VectorField')
    return tools._add_data(data_source, name)


def scalarscatter(*args, **kwargs):
    """
    Creates scattered scalar data. 
    
    **Function signatures**::

        scalarscatter(s, ...)
        scalarscatter(x, y, z, s, ...)
        scalarscatter(x, y, z, s, ...)
        scalarscatter(x, y, z, f, ...)

    If only 1 array s is passed the x, y and z arrays are assumed to be
    made from the indices of vectors.

    If 4 positional arguments are passed the last one must be an array s, or
    a callable, f, that returns an array.

    **Keyword arguments**:
    
        :name: the name of the vtk object created."""
    x, y, z, s = process_regular_scalars(*args)

    points = numpy.c_[x.ravel(), y.ravel(), z.ravel()]

    if not s == None:
        s = s.ravel()

    data_source = _make_glyph_data(points, None, s)

    name = kwargs.pop('name', 'ScalarScatter')
    return tools._add_data(data_source, name)


def scalarfield(*args, **kwargs):
    """
    Creates a scalar field data.
                      
    **Function signatures**::
    
        scalarfield(s, ...)
        scalarfield(x, y, z, s, ...)
        scalarfield(x, y, z, f, ...)

    If only 1 array s is passed the x, y and z arrays are assumed to be
    made from the indices of arrays.

    If the x, y and z arrays are passed they are supposed to have been
    generated by `numpy.mgrid`. The function builds a scalar field assuming 
    the points are regularily spaced.

    If 4 positional arguments are passed the last one must be an array s, or
    a callable, f, that returns an array.
    
    **Keyword arguments**:

        :name: the name of the vtk object created."""
    x, y, z, s = process_regular_scalars(*args)

    points = numpy.c_[x.ravel(), y.ravel(), z.ravel()]
    dx = x[1, 0, 0] - x[0, 0, 0]
    dy = y[0, 1, 0] - y[0, 0, 0]
    dz = z[0, 0, 1] - z[0, 0, 0]        

    data_source = ArraySource(scalar_data=s,
                    origin=[points[0, 0], points[0, 1], points[0, 2]],
                    spacing=[dx, dy, dz])

    name = kwargs.pop('name', 'ScalarField')
    return tools._add_data(data_source, name)


def linesource(*args, **kwargs):
    """
    Creates line data.
    
    **Function signatures**::
    
        linesource(x, y, z, ...)
        linesource(x, y, z, s, ...)
        linesource(x, y, z, f, ...)

        If 4 positional arguments are passed the last one must be an array s, or
        a callable, f, that returns an array. 

    **Keyword arguments**:
    
        :name: the name of the vtk object created."""
    if len(args)==1:
        raise ValueError, "wrong number of arguments"    
    x, y, z, s = process_regular_scalars(*args)

    points = numpy.c_[x.ravel(), y.ravel(), z.ravel()]
    np = len(points) - 1
    lines  = numpy.zeros((np, 2), 'l')
    lines[:,0] = numpy.arange(0, np-0.5, 1, 'l')
    lines[:,1] = numpy.arange(1, np+0.5, 1, 'l')
    data_source = tvtk.PolyData(points=points, lines=lines)

    if not s == None:
        s = s.ravel()
        data_source.point_data.scalars = s

    name = kwargs.pop('name', 'LineSource')
    return tools._add_data(data_source, name)


def array2dsource(*args, **kwargs):
    """
    Creates 2D regularly-spaced data from a 2D array.
    
    Function signatures
    ___________________

        array2dsource(s, ...)
        array2dsource(x, y, s, ...)
        array2dsource(x, y, f, ...)

    If 3 positional arguments are passed the last one must be an array s, or
    a callable, f, that returns an array.

    If only 1 array s is passed the x, z arrays are assumed to be
    made from the indices of arrays, and a regular data set is created."""
    if len(args) == 1:
        s = args[0]
        nx, ny = s.shape
        data_source = ArraySource(transpose_input_array=True,
                    scalar_data=s,
                    origin=[-nx/2., ny/2., 0],
                    spacing=[1, 1, 1])
    else:
        x, y, s = process_regular_2d_scalars(*args)
        assert len(s.shape)==2, "2D array required"
        nx, ny = s.shape
        xa = numpy.linspace(x.min(), x.max(), nx)
        ya = numpy.linspace(y.min(), y.max(), ny)
        data_source = mlab._create_structured_points_direct(xa, ya)
        s = s.T
        s = s.ravel()
        data_source.point_data.scalars = s
        data_source.scalar_type = 'unsigned_char'
        data_source.number_of_scalar_components = 1

    name = kwargs.pop('name', 'Array2DSource')
    return tools._add_data(data_source, name)


def gridsource(x, y, z, **kwargs):
    """
    Creates grid data.
 
    **Keyword arguments**:
    
        :name: the name of the vtk object created.
        
        :scalars: optional scalar data."""
    scalars = kwargs.pop('scalars', None)
    if scalars is None:
        scalars = z
    name    = kwargs.pop('name', 'GridSource')
    triangles, points = mlab.make_triangles_points(x, y, z, scalars)
    data_source = mlab.make_triangle_polydata(triangles, points, scalars)
    return tools._add_data(data_source, name)

